import config
import sys
from zlapi import ZaloAPI
from zlapi.models import ThreadType

def main():
    # Set console encoding to UTF-8
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    admin_id = config.ADMIN
    
    print("Initializing client with config.py credentials...")
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    latitude = 10.762622
    longitude = 106.660172
    
    test_recipient = "8232275665507342564"
    print(f"Sending location to user {test_recipient}...")
    try:
        res = client.sendLocation(
            latitude=latitude,
            longitude=longitude,
            thread_id=test_recipient,
            thread_type=ThreadType.USER,
            title="Đại học Khoa học Tự nhiên",
            address="227 Nguyễn Văn Cừ, Quận 5, TP.HCM"
        )
        print("Success! Result:", repr(res))
    except Exception as e:
        print("Error sending location:", repr(e))

if __name__ == "__main__":
    main()
