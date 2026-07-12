import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from zlapi import ZaloAPI

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def probe_endpoint(client, url):
    params = {
        "zpw_ver": 645,
        "zpw_type": 30
    }
    payload = {
        "params": client._encode({})
    }
    try:
        response = client._post(url, params=params, data=payload)
        status = response.status_code
        try:
            json_data = response.json()
            err_code = json_data.get("error_code")
            msg = json_data.get("error_message")
        except:
            json_data = response.text[:200]
            err_code = "N/A"
            msg = "Not JSON"
        print(f"URL: {url} -> Status: {status}, error_code: {err_code}, msg: {msg}")
    except Exception as e:
        print(f"URL: {url} -> Exception: {e}")

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    endpoints = [
        "https://tt-chat2-wpa.chat.zalo.me/api/message/location",
        "https://tt-chat2-wpa.chat.zalo.me/api/message/sharelocation",
        "https://tt-chat2-wpa.chat.zalo.me/api/message/sendlocation",
        "https://tt-chat4-wpa.chat.zalo.me/api/message/location",
        "https://tt-chat4-wpa.chat.zalo.me/api/message/sharelocation",
        "https://tt-chat4-wpa.chat.zalo.me/api/message/sendlocation",
        "https://tt-files-wpa.chat.zalo.me/api/message/location",
        "https://tt-files-wpa.chat.zalo.me/api/message/sharelocation"
    ]
    
    for url in endpoints:
        probe_endpoint(client, url)

if __name__ == "__main__":
    main()
