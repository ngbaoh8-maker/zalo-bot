import sys
import time
import json
import config
from zlapi import ZaloAPI
from zlapi.models import ThreadType

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def run_test(client, msg_type, zsource, msg_info):
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
            "msgInfo": json.dumps(msg_info),
            "toId": str(config.ADMIN),
            "imei": client._imei
        }
    }
    
    if zsource is not None:
        payload["params"]["zsource"] = zsource
        
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
        
        return error_code, inner_code, inner_msg
    except Exception as e:
        return -1, -1, str(e)

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    msg_types = [1, 2, 3, 5, 6, 11, 12, 13, 14, 15, 31, 38, 43, 44]
    zsources = [-1, 704, 601, 401, 106, 103, None]
    
    msg_info_variants = [
        # Standard location
        {
            "latitude": 10.762622,
            "longitude": 106.660172,
            "title": "Đại học Khoa học Tự nhiên",
            "description": "227 Nguyễn Văn Cừ, Quận 5, TP.HCM",
            "accuracy": 15
        },
        # Minimal location
        {
            "latitude": 10.762622,
            "longitude": 106.660172
        }
    ]
    
    print("Starting tests...")
    
    successes = []
    
    for msg_info in msg_info_variants:
        for msg_type in msg_types:
            for zsource in zsources:
                outer, inner, msg = run_test(client, msg_type, zsource, msg_info)
                print(f"msgType={msg_type}, zsource={zsource} -> outer={outer}, inner={inner}, msg={msg}")
                if inner == 0:
                    print(f"SUCCESS: msgType={msg_type}, zsource={zsource}, msgInfo keys={list(msg_info.keys())} -> inner={inner}, msg={msg}")
                    successes.append((msg_type, zsource, msg_info))
                time.sleep(0.1)
                
    print("Done. Successes:", successes)

if __name__ == "__main__":
    main()
