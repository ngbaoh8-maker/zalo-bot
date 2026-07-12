import sys
import time
import json
import config
from zlapi import ZaloAPI

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RECIPIENT = "8232275665507342564" # Nguyen Hoang Gia Bao

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
            "toId": str(RECIPIENT),
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
    
    latitude = 11.195921265297931
    longitude = 107.36651484849605
    title = "265 Gia Canh"
    address = "265 Gia Canh, Định Quán, Đồng Nai, Việt Nam"

    variants = [
        # v1: Standard (current implementation)
        ("v1_std", {
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "description": address,
            "accuracy": 15
        }),
        # v2: Flat with isUserLocation
        ("v2_flat_userloc", {
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "description": address,
            "isUserLocation": 1,
            "srcId": "0"
        }),
        # v3: Captured (params stringified)
        ("v3_captured", {
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
        }),
        # v4: Minimal with isUserLocation
        ("v4_min_userloc", {
            "latitude": latitude,
            "longitude": longitude,
            "isUserLocation": 1,
            "srcId": "0"
        })
    ]
    
    for msg_type in [11, 43]:
        print(f"\n--- Testing with msgType = {msg_type} ---")
        for name, v in variants:
            run_variant(client, name, v, msg_type=msg_type)
            time.sleep(0.1)

if __name__ == "__main__":
    main()
