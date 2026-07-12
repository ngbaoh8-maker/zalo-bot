import sys
import time
import json
import config
from zlapi import ZaloAPI

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RECIPIENT = "8232275665507342564"

def send_location_msg(client, msg_info_dict):
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
    response = client._post(url, params=params, data=payload)
    return response.json()

def get_last_msg(client):
    try:
        msgs = client.getLastMsgs()
        if msgs and hasattr(msgs, "msgs"):
            for msg in msgs.msgs:
                if msg.get("idTo") == RECIPIENT or msg.get("uidFrom") == RECIPIENT:
                    return msg
        # If not list of objects
        if isinstance(msgs, dict) and "msgs" in msgs:
            for msg in msgs["msgs"]:
                if msg.get("idTo") == RECIPIENT or msg.get("uidFrom") == RECIPIENT:
                    return msg
    except Exception as e:
        print("Error getting last msg:", e)
    return None

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    latitude = 11.195921265297931
    longitude = 107.36651484849605
    title = "Test Step Title"
    address = "265 Gia Canh, Định Quán, Đồng Nai"
    
    variants = [
        ("V1_lat_long", {
            "lat": latitude,
            "long": longitude,
            "title": title,
            "desc": address
        }),
        ("V2_lat_longitude", {
            "lat": latitude,
            "longitude": longitude,
            "title": title,
            "desc": address
        }),
        ("V3_latitude_longitude", {
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "desc": address
        }),
        ("V4_latitude_long", {
            "latitude": latitude,
            "long": longitude,
            "title": title,
            "desc": address
        })
    ]
    
    for name, payload in variants:
        print(f"\n--- Testing {name} ---")
        send_res = send_location_msg(client, payload)
        print("Send response:", send_res.get("error_code"))
        
        # Wait a bit for server to process
        time.sleep(1.5)
        
        last_msg = get_last_msg(client)
        if last_msg:
            content = last_msg.get("content", {})
            params_str = content.get("params", "")
            print("Received params in message:")
            print(params_str)
        else:
            print("Failed to fetch last message for thread.")
            
        time.sleep(1.0)

if __name__ == "__main__":
    main()
