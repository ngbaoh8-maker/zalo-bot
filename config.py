import json
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

IMEI = 'a6e32c65-4c5a-46ec-82eb-07cf7ed6b8fc-a16ddaab909d2cf27fce353f26dd2ff2'
SESSION_COOKIES = {"nl_b04af40bb0e193acf8a9877592394ada": "tzaoLC8i6lt5q3jLoouL_iROFqpRUN2xbzyT1penVG", "zpdid": "41V-b5tnh3uH4fIHK__0Dn0RbfvG_CWq", "zlogin_session": "kW4JGLyjCnIxFnDDLXTbH-Tj2KHV5cn5w6uKLm5JObsZBmTO3LLbHhWf7qKr8dq", "_zlang": "vn", "zpsid": "eMKnVcAlVqAZUYmFCBKa1RmxBrulj2a4l3yvK33YS6B7QNrCDu876zHf2oetbcKZy5qGSpVHHLkb3WbSPeTc1fH8R3TulmrjW4i5Dn6r2GBNM5LC9xCl6m", "__zi": "3000.QOBlzDCV2uGerkFzm0LJsMNNxlp00HVHOzwXzS485T5atgBq.1", "zpw_sek": "C9xb.458158911.a0.F6EewuhWe4O9bIKh5sPhC4r43biKN4b6SbGA1LHM4LC30oTY1byuKLfV8Lv1MrOIInKd0nKmh3gaPzM_PGnhC0"}
