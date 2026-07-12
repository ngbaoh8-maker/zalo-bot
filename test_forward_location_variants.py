import sys
import time
import json
import config
from zlapi import ZaloAPI
from zlapi.models import ThreadType

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RECIPIENT = "8232275665507342564"

def test_forward(client, name, msg_type, client_id, msg_info):
    params = {
        "zpw_ver": 645,
        "zpw_type": 30,
        "nretry": 0
    }
    
    payload_params = {
        "ttl": 0,
        "msgType": msg_type,
        "clientId": client_id,
        "msgInfo": json.dumps(msg_info),
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
                
        print(f"Variant '{name}' (msgType={msg_type}, clientId_type={type(client_id).__name__}) -> outer: {error_code}, inner: {inner_code}, msg: {inner_msg}")
        return inner_code == 0
    except Exception as e:
        print(f"Variant '{name}' Exception: {e}")
        return False

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    latitude = 11.195921
    longitude = 107.366514
    title = "265 Gia Canh"
    address = "265 Gia Canh, Định Quán, Đồng Nai, Việt Nam"
    
    # Shapes
    msg_info_std = {
        "latitude": latitude,
        "longitude": longitude,
        "title": title,
        "description": address,
        "accuracy": 15
    }
    
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
    
    msg_info_minimal = {
        "latitude": latitude,
        "longitude": longitude
    }
    
    shapes = {
        "std": msg_info_std,
        "captured": msg_info_captured,
        "minimal": msg_info_minimal
    }
    
    cids = [
        str(int(time.time() * 1000)),
        int(time.time() * 1000)
    ]
    
    for s_name, s_val in shapes.items():
        for msg_type in [11, 43]:
            for cid in cids:
                test_forward(client, f"{s_name}", msg_type, cid, s_val)

if __name__ == "__main__":
    main()
