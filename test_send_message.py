import sys
import config
from zlapi import ZaloAPI
from zlapi.models import ThreadType, Message

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    print("Testing sendMessage...")
    try:
        res = client.sendMessage(
            Message(text="Hello from bot DCM! Test message."),
            thread_id=config.ADMIN,
            thread_type=ThreadType.USER
        )
        print("Success! Result:", repr(res))
    except Exception as e:
        print("Error:", repr(e))

if __name__ == "__main__":
    main()
