import json
import os

# Get user context
BOT_USER = os.environ.get('BOT_USER')
if BOT_USER:
    USER_DIR = os.path.join(os.path.dirname(__file__), 'users', BOT_USER)
    os.makedirs(USER_DIR, exist_ok=True)
else:
    USER_DIR = os.path.dirname(__file__)

def read_setting_value(key):
    try:
        path = os.path.join(USER_DIR, 'seting.json')
        if not os.path.exists(path) and BOT_USER:
            # Fallback to root settings if user-specific settings don't exist yet
            path = os.path.join(os.path.dirname(__file__), 'seting.json')
            
        with open(path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        return settings.get(key)
    except Exception:
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

def load_session():
    try:
        session_path = os.path.join(USER_DIR, 'session.json')
        if os.path.exists(session_path):
            with open(session_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('imei', ''), data.get('cookies', {})
    except Exception:
        pass
    return '', {}

IMEI, SESSION_COOKIES = load_session()
