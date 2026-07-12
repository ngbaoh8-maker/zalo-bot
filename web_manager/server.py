import os
import sys

# Configure UTF-8 encoding for standard streams
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import json
import shutil
import threading
import time

# Add parent directory to python path for importing zlapi
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify, request, Response
from zlapi import ZaloAPI
from bot_runner import BotRunner

app = Flask(__name__, template_folder='templates', static_folder='static')

# Root bot folder is parent of this folder
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bot_runner = BotRunner(ROOT_DIR)

# Global Zalo QR Login state
qr_login_state = {
    "status": "idle",       # idle, generating, generated, scanned, success, failed
    "image_path": "",
    "error_message": "",
    "user_info": None
}
qr_thread = None
qr_api_instance = None

def save_login_to_config(cookies, imei):
    config_path = os.path.join(ROOT_DIR, 'config.py')
    
    # Read existing config content to preserve GEMINI_API_KEY and other parameters if possible
    # but rewrite standard parameters
    content = f"""import json
import os

def read_setting_value(key):
    try:
        path = os.path.join(os.path.dirname(__file__), 'seting.json')
        with open(path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        return settings.get(key)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

def read_prefix():
    return read_setting_value('prefix') or "?"

def read_admin():
    return read_setting_value('admin') or "4589338218238535959"

API_KEY = 'api_key'
SECRET_KEY = 'secret_key'
PREFIX = read_prefix()
ADMIN = read_admin()
GEMINI_API_KEY = "AIzaSyBiKqIS4xlwQHMlsv7MLzeRoYl_5ppalSU"

# Telegram configuration (optional)
TELEGRAM_BOT_TOKEN = None  
TELEGRAM_CHAT_ID = None    
ENABLE_TELEGRAM = False    

IMEI = {repr(imei)}
SESSION_COOKIES = {json.dumps(cookies)}
"""
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)

def qr_login_worker():
    global qr_login_state, qr_api_instance
    try:
        qr_login_state["status"] = "generating"
        qr_login_state["error_message"] = ""
        qr_login_state["user_info"] = None
        
        static_qr_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        os.makedirs(static_qr_dir, exist_ok=True)
        qr_dest_path = os.path.join(static_qr_dir, 'zalo_qr.png')
        
        # Remove old QR image if exists
        if os.path.exists(qr_dest_path):
            try:
                os.remove(qr_dest_path)
            except Exception:
                pass
                
        qr_login_state["image_path"] = ""

        # Initialize ZaloAPI with no credentials
        qr_api_instance = ZaloAPI("", "", "", auto_login=False)

        def on_qr_gen(path):
            qr_login_state["status"] = "generated"
            qr_login_state["image_path"] = "/static/zalo_qr.png"

        # Start QR login flow (blocking wait for scan and confirm)
        result = qr_api_instance.loginWithQR(
            qr_path=qr_dest_path,
            on_qr_generated=on_qr_gen
        )

        if result and result.get("status") == "success":
            cookies = qr_api_instance._state.get_cookies()
            imei = qr_api_instance._state.user_imei or qr_api_instance._imei
            
            # Save session to config.py
            save_login_to_config(cookies, imei)
            
            qr_login_state["status"] = "success"
            qr_login_state["user_info"] = result.get("userInfo")
        else:
            qr_login_state["status"] = "failed"
            qr_login_state["error_message"] = "Đăng nhập không thành công."
            
    except Exception as e:
        qr_login_state["status"] = "failed"
        qr_login_state["error_message"] = str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/qr/generate', methods=['POST'])
def generate_qr():
    global qr_thread, qr_login_state
    if qr_login_state["status"] in ["generating", "generated"]:
        return jsonify({"status": qr_login_state["status"], "image_path": qr_login_state["image_path"]})
        
    qr_login_state["status"] = "generating"
    qr_thread = threading.Thread(target=qr_login_worker, daemon=True)
    qr_thread.start()
    return jsonify({"status": "generating"})

@app.route('/api/qr/status', methods=['GET'])
def get_qr_status():
    return jsonify(qr_login_state)

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    setting_path = os.path.join(ROOT_DIR, 'seting.json')
    if request.method == 'POST':
        data = request.json
        bot_name = data.get('bot_name', 'Zalo Bot')
        admin_id = data.get('admin_id', '')
        prefix = data.get('prefix', '?')
        
        # Save to file
        settings = {}
        if os.path.exists(setting_path):
            try:
                with open(setting_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except Exception:
                pass
                
        settings['name_bot'] = bot_name
        settings['admin'] = admin_id
        settings['prefix'] = prefix
        
        with open(setting_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
            
        return jsonify({"status": "success", "message": "Đã lưu cấu hình!"})
    else:
        settings = {}
        if os.path.exists(setting_path):
            try:
                with open(setting_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except Exception:
                pass
        return jsonify({
            "bot_name": settings.get("name_bot", "Zalo Bot"),
            "admin_id": settings.get("admin", ""),
            "prefix": settings.get("prefix", "?")
        })

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    data = request.json
    bot_name = data.get('bot_name', 'Zalo Bot')
    admin_id = data.get('admin_id', '')
    prefix = data.get('prefix', '?')
    
    success, message = bot_runner.start(bot_name, admin_id, prefix)
    return jsonify({"status": "success" if success else "error", "message": message})

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    success, message = bot_runner.stop()
    return jsonify({"status": "success" if success else "error", "message": message})

@app.route('/api/bot/status', methods=['GET'])
def get_bot_status():
    return jsonify({
        "running": bot_runner.is_running()
    })

@app.route('/api/bot/logs', methods=['GET'])
def get_bot_logs():
    return jsonify({
        "logs": bot_runner.get_logs()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"Khoi dong Web Manager tai http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
