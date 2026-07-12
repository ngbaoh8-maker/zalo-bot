import sys
import time
import json
import config
from zlapi import ZaloAPI
from zlapi.models import ThreadType

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RECIPIENT = "8232275665507342564" # Nguyen Hoang Gia Bao

def send_link_variant(client, name, type_val, href_val, thumb_val, title_val, desc_val, params_val):
    params = {
        "zpw_ver": 645,
        "zpw_type": 30
    }
    
    payload_params = {
        "msg": "",
        "href": href_val,
        "src": "zalo.me" if "zalo.me" in href_val else "google.com",
        "title": title_val,
        "desc": desc_val,
        "thumb": thumb_val,
        "type": type_val,
        "params": json.dumps(params_val) if params_val else "",
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
                
        print(f"Variant '{name}' (href='{href_val}') -> outer: {error_code}, inner: {inner_code}, msg: {inner_msg}")
        return inner_code == 0
    except Exception as e:
        print(f"Variant '{name}' Exception: {e}")
        return False

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    coords = {
        "isUserLocation": 1,
        "srcId": "0",
        "latitude": 11.195921265297931,
        "longitude": 107.36651484849605
    }
    
    address = "265 Gia Canh, Định Quán, Đồng Nai, Việt Nam"
    
    # Try different href values to see if they pass Zalo validation and how they display
    variants = [
        ("zalo_home", "https://zalo.me"),
        ("zalo_chat", "https://chat.zalo.me"),
        ("zalo_maps", "https://maps.zalo.me"),
        ("google_maps_short", "https://maps.app.goo.gl/xyz"),
        ("zalo_sub_slash", "https://zalo.me/"),
        ("empty_spaces", " "),
        ("dot", ".")
    ]
    
    for name, href in variants:
        send_link_variant(
            client=client,
            name=name,
            type_val=43,
            href_val=href,
            thumb_val="https://maps.gstatic.com/tactile/pane/default_geocode-2x.png",
            title_val="Chia sẻ vị trí",
            desc_val=address,
            params_val=coords
        )
        time.sleep(0.5)

if __name__ == "__main__":
    main()
