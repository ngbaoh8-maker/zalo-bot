import sys
import time
import json
import config
from zlapi import ZaloAPI
from zlapi.models import ThreadType

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def test_group_lon(client):
    try:
        groups = list(client.fetchAllGroups().gridVerMap.keys())
        if not groups:
            print("No groups found to test with.")
            return
        
        target_group = groups[0]
        print(f"Testing location send to group using msgType 7: {target_group}")
        
        params = {
            "zpw_ver": 645,
            "zpw_type": 30,
            "nretry": 0
        }
        
        payload_params = {
            "ttl": 0,
            "msgType": 7,
            "clientId": int(time.time() * 1000),
            "msgInfo": json.dumps({
                "lat": 11.195921265297931,
                "lon": 107.36651484849605,
                "title": "Group Test Lon Title",
                "desc": "265 Gia Canh, Định Quán, Đồng Nai"
            }),
            "grid": str(target_group),
            "visibility": 0,
            "imei": client._imei
        }
        
        payload = {
            "params": client._encode(payload_params)
        }
        
        url = "https://tt-files-wpa.chat.zalo.me/api/group/forward"
        response = client._post(url, params=params, data=payload)
        send_res = response.json()
        print("Group Send response:", send_res)
        
    except Exception as e:
        print(f"Exception: {e}")

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    test_group_lon(client)

if __name__ == "__main__":
    main()
