import sys
import time
import json
import config
from zlapi import ZaloAPI
from zlapi.models import ThreadType

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def run_variant(client, name, msg_info_dict, msg_type=11):
    params = {
        "zpw_ver": 645,
        "zpw_type": 30,
        "nretry": 0
    }
    
    payload = {
        "params": {
            "ttl": 0,
            "msgType": msg_type,
            "clientId": int(time.time() * 1000),
            "msgInfo": json.dumps(msg_info_dict),
            "toId": "8232275665507342564",
            "imei": client._imei
        }
    }
    
    # Encode payload params
    payload["params"] = client._encode(payload["params"])
    
    url = "https://tt-files-wpa.chat.zalo.me/api/message/forward"
    try:
        response = client._post(url, params=params, data=payload)
        data = response.json()
        error_code = data.get("error_code")
        error_message = data.get("error_message")
        
        inner_code = -999
        inner_msg = ""
        results = data.get("data") if error_code == 0 else None
        if results:
            results = client._decode(results)
            results = results.get("data") if results.get("data") else results
            if isinstance(results, str):
                try:
                    results = json.loads(results)
                except:
                    pass
            if isinstance(results, dict):
                inner_code = results.get("error_code")
                inner_msg = results.get("error_message") or results.get("data")
        
        print(f"Variant '{name}' (msgType={msg_type}): outer_err={error_code}, inner_err={inner_code}, inner_msg={inner_msg}")
        if inner_code == 0:
            print("  ACTUAL SUCCESS!!!")
            return True
    except Exception as e:
        print(f"Variant '{name}' Exception: {e}")
    return False

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    variants = [
        # 1. Standard (what we currently have)
        {
            "latitude": 10.762622,
            "longitude": 106.660172,
            "title": "Test Title",
            "description": "Test Desc",
            "accuracy": 15
        },
        # 2. Coordinates as strings
        {
            "latitude": "10.762622",
            "longitude": "106.660172",
            "title": "Test Title",
            "description": "Test Desc",
            "accuracy": 15
        },
        # 3.lat / lng as floats
        {
            "lat": 10.762622,
            "lng": 106.660172,
            "title": "Test Title",
            "description": "Test Desc",
            "accuracy": 15
        },
        # 4. lat / lng as strings
        {
            "lat": "10.762622",
            "lng": "106.660172",
            "title": "Test Title",
            "description": "Test Desc",
            "accuracy": 15
        },
        # 5. without accuracy
        {
            "latitude": 10.762622,
            "longitude": 106.660172,
            "title": "Test Title",
            "description": "Test Desc"
        },
        # 6. Minimal
        {
            "latitude": 10.762622,
            "longitude": 106.660172
        },
        # 7. lat/lng minimal
        {
            "lat": 10.762622,
            "lng": 106.660172
        },
        # 8. lat/lon as floats
        {
            "lat": 10.762622,
            "lon": 106.660172,
            "title": "Test Title",
            "description": "Test Desc"
        },
        # 9. desc instead of description
        {
            "latitude": 10.762622,
            "longitude": 106.660172,
            "title": "Test Title",
            "desc": "Test Desc",
            "accuracy": 15
        }
    ]
    
    for msg_type in [11, 43]:
        print(f"\n--- Testing with msgType = {msg_type} ---")
        for i, v in enumerate(variants):
            run_variant(client, f"v{i+1}", v, msg_type=msg_type)

if __name__ == "__main__":
    main()
