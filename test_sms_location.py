import sys
import time
import json
import config
from zlapi import ZaloAPI
from zlapi.models import ThreadType

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RECIPIENT = "8232275665507342564"

def test_sms_variant(client, name, extra_params):
    params = {
        "zpw_ver": 645,
        "zpw_type": 30,
        "nretry": 0
    }
    
    payload_params = {
        "message": "",
        "clientId": int(time.time() * 1000),
        "imei": client._imei,
        "ttl": 0,
        "toid": str(RECIPIENT)
    }
    payload_params.update(extra_params)
    
    payload = {
        "params": client._encode(payload_params)
    }
    
    url = "https://tt-chat2-wpa.chat.zalo.me/api/message/sms"
    try:
        response = client._post(url, params=params, data=payload)
        data = response.json()
        error_code = data.get("error_code")
        
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
                
        print(f"[{name}] outer: {error_code}, inner: {inner_code}, msg: {inner_msg}")
        return inner_code == 0
    except Exception as e:
        print(f"[{name}] Exception: {e}")
        return False

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    latitude = 11.195921265297931
    longitude = 107.36651484849605
    title = "Trà Sữa Định Quán"
    address = "265 Gia Canh, Định Quán, Đồng Nai"
    
    coords = {
        "isUserLocation": 1,
        "srcId": "0",
        "latitude": latitude,
        "longitude": longitude
    }
    
    # Let's try different combinations of keys
    
    # 1. msgType 43 with msgInfo dict
    test_sms_variant(client, "sms_v1_type43_dict", {
        "msgType": 43,
        "msgInfo": {
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "description": address,
            "accuracy": 15
        }
    })
    
    # 2. msgType 43 with msgInfo stringified JSON
    test_sms_variant(client, "sms_v2_type43_json", {
        "msgType": 43,
        "msgInfo": json.dumps({
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "description": address,
            "accuracy": 15
        })
    })

    # 3. msgType 43 with captured structure
    test_sms_variant(client, "sms_v3_captured_json", {
        "msgType": 43,
        "msgInfo": json.dumps({
            "title": title,
            "description": address,
            "href": "",
            "thumb": "",
            "childnumber": 0,
            "action": "",
            "params": json.dumps(coords),
            "type": ""
        })
    })

    # 4. msgType 43 with properties/propertyExt/content
    test_sms_variant(client, "sms_v4_content", {
        "msgType": 43,
        "content": json.dumps({
            "title": title,
            "description": address,
            "href": "",
            "thumb": "",
            "childnumber": 0,
            "action": "",
            "params": json.dumps(coords),
            "type": ""
        })
    })

if __name__ == "__main__":
    main()
