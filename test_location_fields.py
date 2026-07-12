import sys
import time
import json
import config
from zlapi import ZaloAPI

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RECIPIENT = "8232275665507342564"

def test_fields(client, name, msg_info_dict):
    params = {
        "zpw_ver": 645,
        "zpw_type": 30,
        "nretry": 0
    }
    
    payload_params = {
        "ttl": 0,
        "msgType": 7,
        "clientId": int(time.time() * 1000),
        "msgInfo": json.dumps(msg_info_dict),
        "toId": str(RECIPIENT),
        "imei": client._imei
    }
    
    payload = {
        "params": client._encode(payload_params)
    }
    
    url = "https://tt-files-wpa.chat.zalo.me/api/message/forward"
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
    title = "Test Fields Title"
    address = "265 Gia Canh, Định Quán, Đồng Nai"
    
    variants = {
        "V1_lat_long": {
            "lat": latitude,
            "long": longitude,
            "title": title,
            "desc": address
        },
        "V2_lat_longitude": {
            "lat": latitude,
            "longitude": longitude,
            "title": title,
            "desc": address
        },
        "V3_latitude_longitude": {
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "desc": address
        },
        "V4_latitude_long": {
            "latitude": latitude,
            "long": longitude,
            "title": title,
            "desc": address
        }
    }
    
    for name, payload in variants.items():
        test_fields(client, name, payload)
        time.sleep(0.5)

if __name__ == "__main__":
    main()
