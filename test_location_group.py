import sys
import time
import json
import config
from zlapi import ZaloAPI
from zlapi.models import ThreadType

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def test_group_location(client):
    try:
        groups = list(client.fetchAllGroups().gridVerMap.keys())
        if not groups:
            print("No groups found to test with.")
            return
        
        target_group = groups[0]
        print(f"Testing location send to group using sendLocation: {target_group}")
        
        res = client.sendLocation(
            latitude=11.195921,
            longitude=107.366514,
            thread_id=target_group,
            thread_type=ThreadType.GROUP,
            title="265 Gia Canh",
            address="265 Gia Canh, Định Quán, Đồng Nai, Việt Nam"
        )
        print("Success! Result:", repr(res))
            
    except Exception as e:
        print(f"Exception: {e}")

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    client = ZaloAPI("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    test_group_location(client)

if __name__ == "__main__":
    main()
