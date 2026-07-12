import sys
import time
import json
import config
from zlapi import ZaloAPI

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RECIPIENT = "8232275665507342564" # Nguyen Hoang Gia Bao

def test_combination(client, name, msg_info_dict, msg_type, zsource):
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
    
    if zsource is not None:
        payload_params["zsource"] = zsource
        
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
        
        return error_code, inner_code, inner_msg
    except Exception as e:
        return -1, -1, str(e)

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    latitude = 11.195921265297931
    longitude = 107.36651484849605
    title = "265 Gia Canh"
    address = "265 Gia Canh, Định Quán, Đồng Nai, Việt Nam"
    
    # Define payload shapes
    shapes = {
        "v1_std": {
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "description": address,
            "accuracy": 15
        },
        "v2_flat_userloc": {
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "description": address,
            "isUserLocation": 1,
            "srcId": "0"
        },
        "v3_captured_empty_title": {
            "title": "",
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
        },
        "v3_captured_with_title": {
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
        },
        "v4_min_userloc": {
            "latitude": latitude,
            "longitude": longitude,
            "isUserLocation": 1,
            "srcId": "0"
        }
    }
    
    msg_types = [11, 43]
    zsources = [None, -1, 101, 106, 601, 704]
    
    print("Running comprehensive location tests...")
    
    successes = []
    
    for shape_name, msg_info in shapes.items():
        for msg_type in msg_types:
            for zsource in zsources:
                outer, inner, msg = test_combination(client, shape_name, msg_info, msg_type, zsource)
                
                if inner == 0:
                    print(f"SUCCESS! Shape: {shape_name}, msgType: {msg_type}, zsource: {zsource} -> inner_err={inner}")
                    successes.append((shape_name, msg_type, zsource))
                else:
                    print(f"Fail: Shape={shape_name}, msgType={msg_type}, zsource={zsource} -> outer={outer}, inner={inner}: {msg}")
                time.sleep(0.1)
                
    print("\n--- Test Complete ---")
    print("Successes:", successes)

if __name__ == "__main__":
    main()
