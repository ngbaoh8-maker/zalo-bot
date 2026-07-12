import sys
import time
import json
import config
from zlapi import ZaloAPI

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RECIPIENT = "8232275665507342564" # Nguyen Hoang Gia Bao

def test_link_key(client, key_name):
    params = {
        "zpw_ver": 645,
        "zpw_type": 30
    }
    
    payload_params = {
        "msg": "Test link with " + key_name,
        "href": "https://maps.google.com/?q=11.195921,107.366514",
        "src": "google.com",
        "title": "265 Gia Canh",
        "desc": "265 Gia Canh, Định Quán, Đồng Nai, Việt Nam",
        "thumb": "https://maps.gstatic.com/tactile/pane/default_geocode-2x.png",
        "type": 0,
        "media": json.dumps({
            "type": 0,
            "count": 0,
            "mediaTitle": "",
            "artist": "",
            "streamUrl": "",
            "stream_icon": ""
        }),
        "ttl": 0,
        "clientId": int(time.time() * 1000)
    }
    
    payload_params[key_name] = str(RECIPIENT)
    
    payload = {
        "params": client._encode(payload_params)
    }
    
    url = "https://tt-chat4-wpa.chat.zalo.me/api/message/link"
    try:
        response = client._post(url, params=params, data=payload)
        data = response.json()
        error_code = data.get("error_code")
        
        results = data.get("data") if error_code == 0 else None
        if results:
            results = client._decode(results)
            print(f"Decoded results for {key_name}: {results}")
        else:
            print(f"No data returned for {key_name}, response data: {data}")
    except Exception as e:
        print(f"Key: {key_name} -> Exception: {e}")

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    print("\nTesting with key 'toId'...")
    test_link_key(client, "toId")

if __name__ == "__main__":
    main()
