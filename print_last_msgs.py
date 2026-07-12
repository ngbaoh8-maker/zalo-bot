import sys
import json
import config
from zlapi import ZaloAPI

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    try:
        msgs = client.getLastMsgs()
        print("Last Messages JSON:")
        # msgs is a User defaultmunch object
        print(json.dumps(msgs, indent=4, ensure_ascii=False))
    except Exception as e:
        print("Error getting last msgs:", repr(e))

if __name__ == "__main__":
    main()
