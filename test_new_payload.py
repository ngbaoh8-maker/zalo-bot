import sys
import time
import json
import config
from zlapi import ZaloAPI
from zlapi.models import ThreadType

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def test_payload(client, name, msg_info_dict, msg_type=43, zsource=None):
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
            "toId": str(config.ADMIN),
            "imei": client._imei
        }
    }
    
    if zsource is not None:
        payload["params"]["zsource"] = zsource
        
    # Encode payload params
    payload["params"] = client._encode(payload["params"])
    
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
        
        print(f"[{name}] msgType={msg_type}, zsource={zsource}: outer_err={error_code}, inner_err={inner_code}, inner_msg={inner_msg}")
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
    title = "Test Location Title"
    address = "265 Gia Canh, Định Quán, Đồng Nai, Việt Nam"
    
    # Variant A: params is a serialized string
    msg_info_a = {
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
    
    # Variant B: params is a dictionary (in case Zalo SDK parses it if nested)
    msg_info_b = {
        "title": title,
        "description": address,
        "href": "",
        "thumb": "",
        "childnumber": 0,
        "action": "",
        "params": {
            "isUserLocation": 1,
            "srcId": "0",
            "latitude": latitude,
            "longitude": longitude
        },
        "type": ""
    }
    
    print("Testing Variant A (serialized params string)...")
    test_payload(client, "Variant A (msgType=43)", msg_info_a, msg_type=43)
    test_payload(client, "Variant A (msgType=11)", msg_info_a, msg_type=11)
    
    print("\nTesting Variant B (nested dict)...")
    test_payload(client, "Variant B (msgType=43)", msg_info_b, msg_type=43)
    test_payload(client, "Variant B (msgType=11)", msg_info_b, msg_type=11)

if __name__ == "__main__":
    main()
