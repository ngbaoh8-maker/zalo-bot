import sys
import config
from zlapi import ZaloAPI
from zlapi.models import ThreadType

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    latitude = 11.195921265297931
    longitude = 107.36651484849605
    title = "Đại học Khoa học Tự nhiên"
    address = "227 Nguyễn Văn Cừ, Quận 5, TP.HCM"
    
    link_url = f"https://www.google.com/maps/place/{latitude},{longitude}"
    
    print("Testing sendLink as a fallback for location...")
    try:
        res = client.sendLink(
            linkUrl=link_url,
            title=title,
            thread_id=config.ADMIN,
            thread_type=ThreadType.USER,
            domainUrl="google.com",
            desc=address,
            thumbnailUrl="https://maps.gstatic.com/tactile/pane/default_geocode-2x.png"
        )
        print("Success! Result:", repr(res))
    except Exception as e:
        print("Error:", repr(e))

if __name__ == "__main__":
    main()
