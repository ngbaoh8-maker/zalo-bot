import sys
import time
import json
import config
from zlapi import ZaloAPI

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RECIPIENT = "8232275665507342564" # Nguyen Hoang Gia Bao

def test_variant(client, name, msg_info_dict):
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
                
        print(f"[{name}] outer: {error_code}, inner: {inner_code}, msg: {inner_msg}")
        return inner_code == 0
    except Exception as e:
        print(f"[{name}] Exception: {e}")
        return False

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    latitude = 11.195921265297931
    longitude = 107.36651484849605
    title = "Trà Sữa Định Quán"
    address = "265 Gia Canh, Định Quán, Đồng Nai"
    
    # Let's try many different shapes for type 7
    variants = {
        # Shape A: Flat latitude/longitude standard
        "A_std": {
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "description": address,
            "accuracy": 15
        },
        # Shape B: Flat with isUserLocation
        "B_flat_userloc": {
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "description": address,
            "isUserLocation": 1,
            "srcId": "0"
        },
        # Shape C: Minimal coordinates
        "C_coords_only": {
            "latitude": latitude,
            "longitude": longitude
        },
        # Shape D: lat/lng format
        "D_lat_lng": {
            "lat": latitude,
            "lng": longitude,
            "title": title,
            "desc": address
        },
        # Shape E: Captured incoming format
        "E_captured": {
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
        # Shape F: Captured format but empty fields
        "F_captured_empty": {
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
        # Shape G: Like business card but for location?
        "G_loc_card": {
            "desc": address,
            "latitude": str(latitude),
            "longitude": str(longitude)
        },
        # Shape H: Just coordinates as strings
        "H_coords_str": {
            "latitude": str(latitude),
            "longitude": str(longitude)
        },
        # Shape I: Properties/propertyExt inside msgInfo?
        "I_with_properties": {
            "title": title,
            "description": address,
            "params": json.dumps({
                "isUserLocation": 1,
                "srcId": "0",
                "latitude": latitude,
                "longitude": longitude
            }),
            "properties": {
                "color": -1,
                "size": -1,
                "type": 1,
                "subType": 0,
                "ext": json.dumps({"shouldParseLinkOrContact": 0})
            }
        }
    }
    
    for name, payload in variants.items():
        test_variant(client, name, payload)
        time.sleep(0.2)

if __name__ == "__main__":
    main()
