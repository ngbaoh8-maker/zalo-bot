import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
import config
from zlapi import ZaloAPI

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RECIPIENT = "8232275665507342564" # Nguyen Hoang Gia Bao

def send_location_test(client, name, type_val, href_val, thumb_val, title_val, desc_val, coords_dict):
    params = {
        "zpw_ver": 645,
        "zpw_type": 30
    }
    
    payload_params = {
        "msg": "",
        "href": href_val,
        "src": "google.com",
        "title": title_val,
        "desc": desc_val,
        "thumb": thumb_val,
        "type": type_val,
        "params": json.dumps(coords_dict) if coords_dict else "",
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
                
        print(f"Test '{name}' -> outer: {error_code}, inner: {inner_code}, msg: {inner_msg}")
        return inner_code == 0
    except Exception as e:
        print(f"Test '{name}' Exception: {e}")
        return False

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    latitude = 11.195921265297931
    longitude = 107.36651484849605
    
    coords = {
        "isUserLocation": 1,
        "srcId": "0",
        "latitude": latitude,
        "longitude": longitude
    }
    
    # Let's send 4 distinct variants to the user and ask them which one renders as a native map.
    # We will use distinct titles so they can identify them in the chat.
    
    # Test 1: Google Maps URL + Type 43 + Empty Thumb + Params
    send_location_test(
        client=client,
        name="T1_EmptyThumb_Type43",
        type_val=43,
        href_val=f"https://maps.google.com/?q={latitude},{longitude}",
        thumb_val="",
        title_val="T1 Trà Sữa Định Quán (Empty Thumb)",
        desc_val="265 Gia Canh, Định Quán, Đồng Nai",
        coords_dict=coords
    )
    time.sleep(1.0)
    
    # Test 2: Google Maps Search URL + Type 43 + Empty Thumb + Params
    send_location_test(
        client=client,
        name="T2_GmapsSearch_Type43",
        type_val=43,
        href_val=f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}",
        thumb_val="",
        title_val="T2 Trà Sữa Định Quán (Search URL)",
        desc_val="265 Gia Canh, Định Quán, Đồng Nai",
        coords_dict=coords
    )
    time.sleep(1.0)
    
    # Test 3: Google Maps URL + Type 11 + Empty Thumb + Params
    send_location_test(
        client=client,
        name="T3_EmptyThumb_Type11",
        type_val=11,
        href_val=f"https://maps.google.com/?q={latitude},{longitude}",
        thumb_val="",
        title_val="T3 Trà Sữa Định Quán (Type 11)",
        desc_val="265 Gia Canh, Định Quán, Đồng Nai",
        coords_dict=coords
    )
    time.sleep(1.0)

    # Test 4: Google Maps URL + Type 43 + Google static map (no key) URL as thumb
    # Let's see if Google Static Maps works without key or if we can use another static map service
    static_map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={latitude},{longitude}&zoom=15&size=500x300&markers=color:red%7C{latitude},{longitude}"
    send_location_test(
        client=client,
        name="T4_StaticMapThumb_Type43",
        type_val=43,
        href_val=f"https://maps.google.com/?q={latitude},{longitude}",
        thumb_val=static_map_url,
        title_val="T4 Trà Sữa Định Quán (Static Map Thumb)",
        desc_val="265 Gia Canh, Định Quán, Đồng Nai",
        coords_dict=coords
    )

if __name__ == "__main__":
    main()
