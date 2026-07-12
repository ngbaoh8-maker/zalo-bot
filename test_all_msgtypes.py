import sys
import time
import json
import config
from zlapi import ZaloAPI

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RECIPIENT = "8232275665507342564"

def test_forward_msgtype(client, msg_type, msg_info_dict):
    params = {
        "zpw_ver": 645,
        "zpw_type": 30,
        "nretry": 0
    }
    
    payload_params = {
        "ttl": 0,
        "msgType": msg_type,
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
                
        print(f"msgType {msg_type}: outer_err={error_code}, inner_err={inner_code}, msg={inner_msg}")
        return inner_code == 0
    except Exception as e:
        print(f"msgType {msg_type} Exception: {e}")
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
    
    captured_msg_info = {
        "title": title,
        "description": address,
        "href": "",
        "thumb": "",
        "childnumber": 0,
        "action": "",
        "params": json.dumps(coords),
        "type": ""
    }
    
    print("Testing forward msgType 1 to 25...")
    for mt in range(1, 26):
        test_forward_msgtype(client, mt, captured_msg_info)
        time.sleep(0.25)

if __name__ == "__main__":
    main()
