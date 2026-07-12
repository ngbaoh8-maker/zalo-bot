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
        print("Type of msgs:", type(msgs))
        if isinstance(msgs, dict):
            # Print keys
            print("Keys:", msgs.keys())
            # Search for the user ID in the keys or values
            for k, v in msgs.items():
                if "8232275665507342564" in str(k) or "8232275665507342564" in str(v):
                    print(f"Found reference in {k}!")
                    print(json.dumps(v, indent=4, ensure_ascii=False)[:3000])
        else:
            print(str(msgs)[:1000])
    except Exception as e:
        print("Error:", repr(e))

if __name__ == "__main__":
    main()
