import json
import os

def read_setting_value(key):
    try:
        path = os.path.join(os.path.dirname(__file__), 'seting.json')
        with open(path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        return settings.get(key)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file seting.json. Sử dụng giá trị mặc định cho {key}.")
        return None
    except json.JSONDecodeError:
        print(f"Lỗi: File seting.json không hợp lệ. Sử dụng giá trị mặc định cho {key}.")
        return None

def read_prefix():
    return read_setting_value('prefix') or "?"

def read_admin():
    return read_setting_value('admin') or "349089207700459683"

IMEI = "4aa2dc15-462e-4b65-b30e-6fcb872307b8-a16ddaab909d2cf27fce353f26dd2ff2"
SESSION_COOKIES = {"nl_b04af40bb0e193acf8a9877592394ada": "tzaoLC8i6ltBsp1Mp2KS-SJRCqlPUdoybTmH03enVG",
  "zpdid": "4HpxarF_f3qH69oIK_l3FnCMbPHNzC8v",
  "zlogin_session": "kW4JGLyjCnIxFnDDLXTbH-Tj1qzK5MjEuMeJN0XNPLQgBWD86r9lLgek24WOKMrQVG",
  "_zlang": "vn",
  "zpsid": "eMKnVcAlVqAZUYmFQOfzNEK3UWbpZ7LUw0Tb37oJ11-PVbitKvjGBBz72nrCf7qIbr0fEnYfHnVgOnOz3Ubz9yOu6t9MktLoer8E872CUJc_UpO3Mvuz64i",
  "__zi": "3000.QOBlzDCV2uGerkFzm09Vrs3Gw__D1XBIRjUl_Sy86zPYrgZp.1",
  "zpw_sek": "Tu5N.396451491.a0._KOPdV1OhGvJ1WmPqLYj3ejwo6NIOezDes7EQDyWzJR279vvbYxfHBWom26XPP0iZNBRVoqEQWHYMOuFbp6j3W"}
API_KEY = 'api_key'
SECRET_KEY = 'secret_key'
PREFIX = read_prefix()
ADMIN = read_admin()
GEMINI_API_KEY = "AIzaSyBiKqIS4xlwQHMlsv7MLzeRoYl_5ppalSU"