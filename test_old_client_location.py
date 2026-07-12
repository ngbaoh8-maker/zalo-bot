import sys
import time
import json
import config
from zlapi.client import ZaloAPI
from zlapi.models import ThreadType

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

RECIPIENT = "8232275665507342564"

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    latitude = 11.195921265297931
    longitude = 107.36651484849605
    title = "Old Client Location Test"
    address = "265 Gia Canh, Định Quán, Đồng Nai"
    
    print("Calling old client's sendLocation...")
    try:
        res = client.sendLocation(
            latitude=latitude,
            longitude=longitude,
            thread_id=RECIPIENT,
            thread_type=ThreadType.USER,
            title=title,
            address=address
        )
        print("Success! Result:", repr(res))
    except Exception as e:
        print("Exception:", repr(e))

if __name__ == "__main__":
    main()
