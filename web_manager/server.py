import os
import sys
import base64
import tempfile
import subprocess
import hashlib

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
from datetime import timedelta

# Add parent directory to python path for importing zlapi
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify, request, Response, session
from zlapi import ZaloAPI
from bot_runner import BotRunner

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'zalo_bot_saas_super_secret_key_9988')
app.permanent_session_lifetime = timedelta(days=365) # 1 year

# Root bot folder is parent of this folder
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bot_runner = BotRunner(ROOT_DIR)

# Global variables for auto-start and watchdog
installing_users = set()

def update_bot_status_setting(username, status):
    user_dir = os.path.join(ROOT_DIR, 'users', username)
    setting_path = os.path.join(user_dir, 'seting.json')
    settings = {}
    if os.path.exists(setting_path):
        try:
            with open(setting_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except Exception:
            pass
    settings['status'] = status
    os.makedirs(user_dir, exist_ok=True)
    with open(setting_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

def auto_start_if_needed(username):
    user_dir = os.path.join(ROOT_DIR, 'users', username)
    setting_path = os.path.join(user_dir, 'seting.json')
    session_path = os.path.join(user_dir, 'session.json')
    
    if os.path.exists(setting_path) and os.path.exists(session_path):
        try:
            with open(setting_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except Exception:
            return
            
        if settings.get('status') == 'running' and not bot_runner.is_running(username):
            bot_name = settings.get('name_bot')
            admin_id = settings.get('admin')
            prefix = settings.get('prefix', '?')
            if bot_name and admin_id:
                bot_runner.log_message(username, "[SYSTEM] 🚀 Thư viện đã cài xong. Tự động khởi chạy lại bot...\n")
                bot_runner.start(username, bot_name, admin_id, prefix)

def bot_watchdog_worker():
    while True:
        try:
            time.sleep(15)
            # Load users dynamically
            users_file = os.path.join(ROOT_DIR, 'database', 'users.json')
            if not os.path.exists(users_file):
                continue
            with open(users_file, 'r', encoding='utf-8') as f:
                users_list = json.load(f)
            
            for user in users_list.keys():
                if user in installing_users:
                    continue # Skip if installing pip packages
                
                user_dir = os.path.join(ROOT_DIR, 'users', user)
                setting_path = os.path.join(user_dir, 'seting.json')
                session_path = os.path.join(user_dir, 'session.json')
                
                if os.path.exists(setting_path) and os.path.exists(session_path):
                    try:
                        with open(setting_path, 'r', encoding='utf-8') as f:
                            settings = json.load(f)
                    except Exception:
                        continue
                        
                    if settings.get('status') == 'running':
                        if not bot_runner.is_running(user):
                            bot_name = settings.get('name_bot')
                            admin_id = settings.get('admin')
                            prefix = settings.get('prefix', '?')
                            if bot_name and admin_id:
                                print(f"[WATCHDOG] Bot cho user '{user}' đang offline. Tu dong khoi chay lai...")
                                bot_runner.log_message(user, "[SYSTEM] 🔄 Phát hiện bot bị dừng đột ngột. Tự động khởi động lại bot...\n")
                                bot_runner.start(user, bot_name, admin_id, prefix)
        except Exception as e:
            print(f"[WATCHDOG ERROR] {e}")

# Start the watchdog thread immediately
threading.Thread(target=bot_watchdog_worker, daemon=True).start()


# User Database Helper Functions
DB_DIR = os.path.join(ROOT_DIR, 'database')
os.makedirs(DB_DIR, exist_ok=True)
USERS_DB = os.path.join(DB_DIR, 'users.json')

def load_users():
    if not os.path.exists(USERS_DB):
        return {}
    try:
        with open(USERS_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users):
    with open(USERS_DB, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Multi-tenant QR Login states
qr_login_states = {}   # username -> state dict
qr_threads = {}        # username -> Thread
qr_api_instances = {}  # username -> ZaloAPI instance

def save_login_to_config(username, cookies, imei, uid=None, name=None):
    user_dir = os.path.join(ROOT_DIR, 'users', username)
    os.makedirs(user_dir, exist_ok=True)
    session_path = os.path.join(user_dir, 'session.json')
    
    # Keep old values if they exist and new ones are not provided
    existing_data = {}
    if os.path.exists(session_path):
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except Exception:
            pass
            
    session_data = {
        "cookies": cookies,
        "imei": imei,
        "uid": uid or existing_data.get("uid"),
        "name": name or existing_data.get("name")
    }
    with open(session_path, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, indent=4, ensure_ascii=False)

def qr_login_worker(username):
    global qr_login_states, qr_api_instances
    tmp_qr_path = None
    try:
        qr_login_states[username] = {
            "status": "generating",
            "qr_base64": "",
            "error_message": "",
            "user_info": None
        }
        
        user_dir = os.path.join(ROOT_DIR, 'users', username)
        os.makedirs(user_dir, exist_ok=True)
        
        # Use temp file for QR
        tmp_fd, tmp_qr_path = tempfile.mkstemp(suffix='.png')
        os.close(tmp_fd)
 
        # Initialize ZaloAPI with no credentials
        api_instance = ZaloAPI("", "", "", auto_login=False)
        qr_api_instances[username] = api_instance
 
        def on_qr_gen(path):
            try:
                with open(path, 'rb') as f:
                    img_data = f.read()
                qr_login_states[username]["qr_base64"] = base64.b64encode(img_data).decode('utf-8')
            except Exception:
                pass
            qr_login_states[username]["status"] = "generated"
 
        # Start QR login flow
        result = api_instance.loginWithQR(
            qr_path=tmp_qr_path,
            on_qr_generated=on_qr_gen
        )
 
        if result and result.get("status") == "success":
            cookies = api_instance._state.get_cookies()
            imei = api_instance._state.user_imei or api_instance._imei
            user_info = result.get("userInfo") or {}
            zalo_uid = user_info.get("uid") or user_info.get("userId")
            zalo_name = user_info.get("name")
            
            # Save session to config.py
            save_login_to_config(username, cookies, imei, zalo_uid, zalo_name)
            
            qr_login_states[username]["status"] = "success"
            qr_login_states[username]["user_info"] = user_info
        else:
            qr_login_states[username]["status"] = "failed"
            qr_login_states[username]["error_message"] = "Đăng nhập không thành công."
            
    except Exception as e:
        qr_login_states[username] = {
            "status": "failed",
            "qr_base64": "",
            "error_message": str(e),
            "user_info": None
        }
    finally:
        if tmp_qr_path and os.path.exists(tmp_qr_path):
            try:
                os.remove(tmp_qr_path)
            except Exception:
                pass

@app.before_request
def require_login():
    # Authenticate API requests, except auth routes and static assets
    if request.path.startswith('/api/') and not request.path.startswith('/api/auth/'):
        if 'username' not in session:
            return jsonify({"status": "error", "message": "Vui lòng đăng nhập để thực hiện chức năng này!"}), 401

@app.route('/')
def index():
    return render_template('index.html')

# ============================
# AUTHENTICATION API ROUTES
# ============================
@app.route('/api/auth/register', methods=['POST'])
def auth_register():
    data = request.json or {}
    username = data.get('username', '').strip().lower()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({"status": "error", "message": "Tên đăng nhập và mật khẩu không được để trống!"})
        
    if len(username) < 3 or len(password) < 6:
        return jsonify({"status": "error", "message": "Tên đăng nhập tối thiểu 3 ký tự, mật khẩu tối thiểu 6 ký tự!"})
        
    users = load_users()
    if username in users:
        return jsonify({"status": "error", "message": "Tên đăng nhập đã tồn tại!"})
        
    users[username] = {
        "password": hash_password(password),
        "created_at": time.time()
    }
    save_users(users)
    return jsonify({"status": "success", "message": "Đăng ký tài khoản thành công!"})

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.json or {}
    username = data.get('username', '').strip().lower()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({"status": "error", "message": "Vui lòng nhập đủ tên đăng nhập và mật khẩu!"})
        
    users = load_users()
    if username not in users or users[username]["password"] != hash_password(password):
        return jsonify({"status": "error", "message": "Tài khoản hoặc mật khẩu không chính xác!"})
        
    session.permanent = True
    session['username'] = username
    return jsonify({"status": "success", "message": "Đăng nhập thành công!", "username": username})

@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    session.clear()
    return jsonify({"status": "success", "message": "Đã đăng xuất!"})

@app.route('/api/auth/session', methods=['GET'])
def auth_session():
    if 'username' in session:
        return jsonify({"logged_in": True, "username": session['username']})
    return jsonify({"logged_in": False})

@app.route('/api/auth/config', methods=['GET'])
def auth_config():
    """Return public configuration for frontend auth setup."""
    return jsonify({
        "google_client_id": os.environ.get('GOOGLE_CLIENT_ID', '')
    })

@app.route('/api/auth/google', methods=['POST'])
def auth_google():
    """Verify Google ID token and auto-login/register user."""
    data = request.json or {}
    credential = data.get('credential', '').strip()
    
    if not credential:
        return jsonify({"status": "error", "message": "Token Google không hợp lệ!"})
    
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    if not GOOGLE_CLIENT_ID:
        return jsonify({"status": "error", "message": "GOOGLE_CLIENT_ID chưa được thiết lập trên server!"})
    
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        
        idinfo = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10
        )
        
        google_id = idinfo['sub']
        email = idinfo.get('email', '')
        name = idinfo.get('name', email)
        
        if not email:
            return jsonify({"status": "error", "message": "Không lấy được email từ tài khoản Google!"})
        
        # Derive a safe username from email: gg_firstname_lastname
        base_username = 'gg_' + email.split('@')[0].lower().replace('.', '_').replace('+', '_')
        
        users = load_users()
        
        # Check if this Google account already registered (by google_id)
        username = None
        for uname, udata in users.items():
            if isinstance(udata, dict) and udata.get('google_id') == google_id:
                username = uname
                break
        
        if not username:
            # First-time Google login - auto-register
            username = base_username
            # Ensure username is unique
            counter = 1
            while username in users:
                username = base_username + str(counter)
                counter += 1
            
            users[username] = {
                "password": None,
                "google_id": google_id,
                "email": email,
                "name": name,
                "created_at": time.time()
            }
            save_users(users)
        
        session.permanent = True
        session['username'] = username
        return jsonify({"status": "success", "message": f"Đăng nhập Google thành công!", "username": username})
    
    except ValueError as e:
        return jsonify({"status": "error", "message": f"Token Google không hợp lệ: {str(e)}"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Đăng nhập Google thất bại: {str(e)}"})

# ============================
# MULTI-TENANT ZALO QR LOGIN
# ============================
@app.route('/api/qr/generate', methods=['POST'])
def generate_qr():
    global qr_threads, qr_login_states
    username = session['username']
    
    state = qr_login_states.get(username, {})
    if state.get("status") in ["generating", "generated"]:
        return jsonify({"status": state["status"], "image_path": ""})
        
    qr_login_states[username] = {"status": "generating"}
    t = threading.Thread(target=qr_login_worker, args=(username,), daemon=True)
    qr_threads[username] = t
    t.start()
    return jsonify({"status": "generating"})

@app.route('/api/qr/status', methods=['GET'])
def get_qr_status():
    username = session['username']
    state = qr_login_states.get(username, {"status": "idle"})
    return jsonify(state)

@app.route('/api/bot/zalo-profile', methods=['GET'])
def get_zalo_profile():
    username = session['username']
    user_dir = os.path.join(ROOT_DIR, 'users', username)
    session_path = os.path.join(user_dir, 'session.json')
    setting_path = os.path.join(user_dir, 'seting.json')
    
    uid = None
    name = None

    # Đọc từ session.json
    if os.path.exists(session_path):
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            uid = data.get('uid') or data.get('userId')
            name = data.get('name')
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})

    # Fallback: đọc uid từ seting.json (field 'admin')
    if not uid and os.path.exists(setting_path):
        try:
            with open(setting_path, 'r', encoding='utf-8') as f:
                seting = json.load(f)
            uid = seting.get('admin')
            if not name:
                name = seting.get('name_bot', 'Zalo Account')
        except Exception:
            pass

    if uid:
        return jsonify({'status': 'success', 'uid': str(uid), 'name': name})
    return jsonify({'status': 'success', 'uid': None, 'name': None})

# ============================
# BOT CONTROL API
# ============================
@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    username = session['username']
    user_dir = os.path.join(ROOT_DIR, 'users', username)
    setting_path = os.path.join(user_dir, 'seting.json')
    
    if request.method == 'POST':
        data = request.json
        bot_name = data.get('bot_name', 'Zalo Bot')
        admin_id = data.get('admin_id', '')
        prefix = data.get('prefix', '?')
        
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
        
        os.makedirs(user_dir, exist_ok=True)
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
    username = session['username']
    data = request.json
    bot_name = data.get('bot_name', 'Zalo Bot')
    admin_id = data.get('admin_id', '')
    prefix = data.get('prefix', '?')
    
    success, message = bot_runner.start(username, bot_name, admin_id, prefix)
    if success:
        update_bot_status_setting(username, 'running')
    return jsonify({"status": "success" if success else "error", "message": message})

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    username = session['username']
    success, message = bot_runner.stop(username)
    if success:
        update_bot_status_setting(username, 'stopped')
    return jsonify({"status": "success" if success else "error", "message": message})

@app.route('/api/bot/restart', methods=['POST'])
def restart_bot():
    username = session['username']
    data = request.json or {}
    bot_name = data.get('bot_name', 'Zalo Bot')
    admin_id = data.get('admin_id', '')
    prefix = data.get('prefix', '?')
    
    if bot_runner.is_running(username):
        bot_runner.stop(username)
        time.sleep(1.5) # Wait for it to shut down properly
        
    success, message = bot_runner.start(username, bot_name, admin_id, prefix)
    if success:
        update_bot_status_setting(username, 'running')
    return jsonify({"status": "success" if success else "error", "message": "Khởi động lại bot thành công!" if success else message})

@app.route('/api/bot/status', methods=['GET'])
def get_bot_status():
    username = session['username']
    return jsonify({
        "running": bot_runner.is_running(username)
    })

@app.route('/api/bot/logs', methods=['GET'])
def get_bot_logs():
    username = session['username']
    return jsonify({
        "logs": bot_runner.get_logs(username)
    })

# ============================
# PIP LIBRARIES MANAGER API
# ============================
@app.route('/api/pip/install', methods=['POST'])
def pip_install():
    username = session['username']
    data = request.json or {}
    package = data.get('package', '').strip()
    if not package:
        return jsonify({"status": "error", "message": "Tên thư viện không được để trống!"})
    
    if any(c in package for c in [';', '&', '|', '`', '$', '>', '<', '\n', '\r']):
        return jsonify({"status": "error", "message": "Tên thư viện không hợp lệ!"})
    
    def run_install():
        installing_users.add(username)
        bot_runner.log_message(username, f"[PIP] Đang cài đặt: {package}...\n")
        try:
            proc = subprocess.Popen(
                [sys.executable, '-m', 'pip', 'install', package, '--no-cache-dir'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            for line in proc.stdout:
                bot_runner.log_message(username, line)
            proc.wait()
            if proc.returncode == 0:
                bot_runner.log_message(username, f"[PIP] ✅ Đã cài đặt thành công: {package}\n")
                auto_start_if_needed(username)
            else:
                bot_runner.log_message(username, f"[PIP] ❌ Cài đặt thất bại: {package} (exit code {proc.returncode})\n")
        except Exception as e:
            bot_runner.log_message(username, f"[PIP ERROR] {e}\n")
        finally:
            installing_users.discard(username)
    
    threading.Thread(target=run_install, daemon=True).start()
    return jsonify({"status": "success", "message": f"Đang cài đặt {package}..."})

@app.route('/api/pip/install-all', methods=['POST'])
def pip_install_all():
    username = session['username']
    req_path = os.path.join(ROOT_DIR, 'requirements.txt')
    if not os.path.exists(req_path):
        return jsonify({"status": "error", "message": "Không tìm thấy requirements.txt!"})
    
    def run_install_all():
        installing_users.add(username)
        bot_runner.log_message(username, "[PIP] 🔄 Bắt đầu cài đặt tất cả thư viện từ requirements.txt...\n")
        try:
            proc = subprocess.Popen(
                [sys.executable, '-m', 'pip', 'install', '-r', req_path, '--no-cache-dir'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            for line in proc.stdout:
                bot_runner.log_message(username, line)
            proc.wait()
            if proc.returncode == 0:
                bot_runner.log_message(username, "[PIP] ✅ Đã cài đặt thành công tất cả thư viện!\n")
                auto_start_if_needed(username)
            else:
                bot_runner.log_message(username, f"[PIP] ❌ Có lỗi khi cài đặt thư viện (exit code {proc.returncode})\n")
        except Exception as e:
            bot_runner.log_message(username, f"[PIP ERROR] {e}\n")
        finally:
            installing_users.discard(username)
    
    threading.Thread(target=run_install_all, daemon=True).start()
    return jsonify({"status": "success", "message": "Đang cài đặt tất cả thư viện..."})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"Khoi dong Web Manager tai http://localhost:{port}")
    
    # Auto-start previously running bots for registered users on startup
    try:
        users_file = os.path.join(ROOT_DIR, 'database', 'users.json')
        if os.path.exists(users_file):
            with open(users_file, 'r', encoding='utf-8') as f:
                users_list = json.load(f)
            
            for user in users_list.keys():
                user_dir = os.path.join(ROOT_DIR, 'users', user)
                setting_path = os.path.join(user_dir, 'seting.json')
                session_path = os.path.join(user_dir, 'session.json')
                
                if os.path.exists(setting_path) and os.path.exists(session_path):
                    with open(setting_path, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                    bot_name = settings.get('name_bot')
                    admin_id = settings.get('admin')
                    prefix = settings.get('prefix', '?')
                    
                    if bot_name and admin_id and settings.get('status') != 'stopped':
                        print(f"[SYSTEM] Tu dong khoi dong bot cho user: {user}")
                        bot_runner.start(user, bot_name, admin_id, prefix)
                        update_bot_status_setting(user, 'running')
    except Exception as e:
        print(f"Loi khoi dong bot tu dong luc startup: {e}")

    app.run(host='0.0.0.0', port=port, debug=False)
