import sys
import time
import json
import config
from zlapi import ZaloAPI
from zlapi.models import ThreadType

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

class TestClient(ZaloAPI):
    def onMessage(self, mid=None, author_id=None, message=None, message_object=None, thread_id=None, thread_type=ThreadType.USER):
        print("\n=== MESSAGE RECEIVED ===")
        print(f"Mid: {mid}")
        print(f"Author ID: {author_id}")
        print(f"Message text: {message}")
        print(f"Thread ID: {thread_id}")
        print(f"Thread Type: {thread_type}")
        print("Message Object Dict:")
        if message_object:
            try:
                # Convert munch/dict to pretty json
                print(json.dumps(message_object, indent=4, ensure_ascii=False))
            except Exception as e:
                print(repr(message_object))
        print("========================\n")

def main():
    session_cookies = config.SESSION_COOKIES
    imei = config.IMEI
    
    print("Logging in...")
    client = TestClient("api_key", "secret_key", imei, session_cookies=session_cookies)
    
    print("Listening... Send a location message to this bot now!")
    # Start listening. Use run_forever=True or similar, or just a while loop if needed.
    # The listen method has a run_forever parameter.
    client.listen(run_forever=True)

if __name__ == "__main__":
    main()
