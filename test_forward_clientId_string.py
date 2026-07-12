import sys
import time
import json
import config
from zlapi import ZaloAPI

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RECIPIENT = "8232275665507342564"

def test_forward_variant(client, name, msg_type, msg_info_dict):
    params = {
        "zpw_ver": 645,
        "zpw_type": 30,
        "nretry": 0
    }
    
    # Using str() for clientId and multiplying by 60 like in working SDK functions
    client_id = str(int(time.time() * 1000) * 60)
    
    payload_params = {
        "ttl": 0,
        "msgType": msg_type,
        "clientId": client_id,
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
                
        print(f"[{name}] msgType={repr(msg_type)} -> outer: {error_code}, inner: {inner_code}, msg: {inner_msg}")
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
    
    # 1. Flat shape (like in zlapi/client.py)
    flat_msg_info = {
        "latitude": latitude,
        "longitude": longitude,
        "title": title,
        "description": address,
        "accuracy": 15
    }
    
    # 2. Captured shape
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
    
    # Test message types 11 and 43 (both as integer and string)
    msg_types = [11, "11", 43, "43"]
    
    print("--- Testing Flat msgInfo shape with ClientId String ---")
    for mt in msg_types:
        test_forward_variant(client, "flat", mt, flat_msg_info)
        time.sleep(0.25)
        
    print("\n--- Testing Captured msgInfo shape with ClientId String ---")
    for mt in msg_types:
        test_forward_variant(client, "captured", mt, captured_msg_info)
        time.sleep(0.25)

if __name__ == "__main__":
    main()
