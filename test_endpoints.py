import sys
import time
import json
import config
from zlapi import ZaloAPI

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def test_endpoint(client, url, msg_type, msg_info, use_toid=True, params_override=None):
    params = {
        "zpw_ver": 645,
        "zpw_type": 30,
        "nretry": 0
    }
    
    payload_params = {
        "ttl": 0,
        "msgType": msg_type,
        "clientId": int(time.time() * 1000),
        "imei": client._imei
    }
    
    test_recipient = "8232275665507342564"
    if use_toid:
        payload_params["toId"] = str(test_recipient)
    else:
        payload_params["toid"] = str(test_recipient)
        
    if isinstance(msg_info, dict):
        payload_params["msgInfo"] = json.dumps(msg_info)
    else:
        payload_params["msgInfo"] = msg_info
        
    if params_override:
        payload_params.update(params_override)
        
    payload = {
        "params": client._encode(payload_params)
    }
    
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
        
        print(f"URL: {url.split('/api/')[-1]} | msgType: {msg_type} -> outer: {error_code}, inner: {inner_code}, msg: {inner_msg}")
        return inner_code == 0
    except Exception as e:
        print(f"URL: {url.split('/api/')[-1]} | msgType: {msg_type} -> Exception: {e}")
        return False

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    latitude = 11.195921265297931
    longitude = 107.36651484849605
    title = "Test Location Title"
    address = "265 Gia Canh, Định Quán, Đồng Nai, Việt Nam"
    
    # 1. Standard format
    msg_info_standard = {
        "latitude": latitude,
        "longitude": longitude,
        "title": title,
        "description": address,
        "accuracy": 15
    }
    
    # 2. Captured format
    msg_info_captured = {
        "title": title,
        "description": address,
        "href": "",
        "thumb": "",
        "childnumber": 0,
        "action": "",
        "params": json.dumps({
            "isUserLocation": 1,
            "srcId": "0",
            "latitude": latitude,
            "longitude": longitude
        }),
        "type": ""
    }
    
    # 3. Minimal format
    msg_info_minimal = {
        "latitude": latitude,
        "longitude": longitude
    }
    
    urls = [
        "https://tt-files-wpa.chat.zalo.me/api/message/forward",
        "https://tt-chat2-wpa.chat.zalo.me/api/message/sms",
        "https://tt-chat4-wpa.chat.zalo.me/api/message/link",
        "https://tt-chat4-wpa.chat.zalo.me/api/message/location",
        "https://tt-chat2-wpa.chat.zalo.me/api/message/location",
        "https://tt-files-wpa.chat.zalo.me/api/message/location"
    ]
    
    payloads = [
        ("standard", msg_info_standard),
        ("captured", msg_info_captured),
        ("minimal", msg_info_minimal)
    ]
    
    msg_types = [11, 43]
    
    for url in urls:
        print(f"\n--- Testing URL: {url} ---")
        for p_name, p_val in payloads:
            for msg_type in msg_types:
                # Try with toId
                test_endpoint(client, url, msg_type, p_val, use_toid=True, params_override={"desc": address, "title": title} if "link" in url else None)
                # Try with toid (lowercase)
                test_endpoint(client, url, msg_type, p_val, use_toid=False, params_override={"desc": address, "title": title} if "link" in url else None)

if __name__ == "__main__":
    main()
