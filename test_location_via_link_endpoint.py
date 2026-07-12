import sys
import time
import json
import config
from zlapi import ZaloAPI

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RECIPIENT = "8232275665507342564" # Nguyen Hoang Gia Bao

def test_location_via_link(client):
    params = {
        "zpw_ver": 645,
        "zpw_type": 30
    }
    
    payload_params = {
        "msg": "Vị trí của tôi",
        "href": "https://maps.google.com/?q=11.195921,107.366514",
        "src": "google.com",
        "title": "265 Gia Canh",
        "desc": "265 Gia Canh, Định Quán, Đồng Nai, Việt Nam",
        "thumb": "https://maps.gstatic.com/tactile/pane/default_geocode-2x.png",
        "type": 0,
        "params": json.dumps({
            "isUserLocation": 1,
            "srcId": "0",
            "latitude": 11.195921265297931,
            "longitude": 107.36651484849605
        }),
        "media": json.dumps({
            "type": 0,
            "count": 0,
            "mediaTitle": "",
            "artist": "",
            "streamUrl": "",
            "stream_icon": ""
        }),
        "ttl": 0,
        "clientId": int(time.time() * 1000),
        "toId": str(RECIPIENT)
    }
    
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
            print(f"Decoded results: {results}")
        else:
            print(f"Failed, response data: {data}")
    except Exception as e:
        print(f"Exception: {e}")

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    test_location_via_link(client)

if __name__ == "__main__":
    main()
