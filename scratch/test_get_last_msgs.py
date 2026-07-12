import sys
import os
# Insert the project root directory at index 0 to override global site-packages
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import config
from zlapi import ZaloAPI

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    print("Calling getLastMsgs...")
    try:
        res = client.getLastMsgs()
        print("getLastMsgs raw response type:", type(res))
        if hasattr(res, '__dict__'):
            print(json.dumps(res.__dict__, indent=2, default=str, ensure_ascii=False))
        else:
            print(res)
    except Exception as e:
        print("Error:", repr(e))

if __name__ == "__main__":
    main()
