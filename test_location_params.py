import sys
import time
import json
import config
from zlapi import ZaloAPI

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def run_test(client, client_id_val, msg_type, zsource, msg_info_dict):
    params = {
        "zpw_ver": 645,
        "zpw_type": 30,
        "nretry": 0
    }
    
    payload_params = {
        "ttl": 0,
        "msgType": msg_type,
        "clientId": client_id_val,
        "msgInfo": json.dumps(msg_info_dict),
        "toId": str(config.ADMIN),
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
    title = "Test Location Title"
    address = "265 Gia Canh, Định Quán, Đồng Nai, Việt Nam"
    
    # msgInfo variants
    msg_infos = {
        # Shape 1: Standard
        "shape1_std": {
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "description": address,
            "accuracy": 15
        },
        # Shape 2: Flat with isUserLocation
        "shape2_flat_userloc": {
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "description": address,
            "isUserLocation": 1,
            "srcId": "0"
        },
        # Shape 3: Captured (params stringified)
        "shape3_captured": {
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
        # Shape 4: Minimal with isUserLocation
        "shape4_min_userloc": {
            "latitude": latitude,
            "longitude": longitude,
            "isUserLocation": 1,
            "srcId": "0"
        }
    }
    
    # Try combinations
    client_ids = [
        str(int(time.time() * 1000)), # String ms timestamp
        int(time.time() * 1000)        # Integer ms timestamp
    ]
    
    msg_types = [11, 43]
    zsources = [None, 106, 704, 601]
    
    print("Starting parameter tests...")
    
    successes = []
    
    for shape_name, msg_info in msg_infos.items():
        for cid in client_ids:
            cid_type = "str" if isinstance(cid, str) else "int"
            for msg_type in msg_types:
                for zsource in zsources:
                    outer, inner, msg = run_test(client, cid, msg_type, zsource, msg_info)
                    
                    if inner == 0:
                        print(f"SUCCESS! Shape: {shape_name}, ClientId Type: {cid_type}, msgType: {msg_type}, zsource: {zsource} -> inner_err={inner}")
                        successes.append((shape_name, cid_type, msg_type, zsource))
                    else:
                        # Print failures to see progress
                        print(f"Fail: Shape={shape_name}, cid={cid_type}, msgType={msg_type}, zsource={zsource} -> inner={inner}: {msg}")
                    time.sleep(0.05)
                    
    print("\n--- Test Complete ---")
    print("Successes:", successes)

if __name__ == "__main__":
    main()
