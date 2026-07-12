import sys
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

def get_sms_messages(phone_number):
    url = f"https://sms-online.co/receive-free-sms/{phone_number}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return []
        
    soup = BeautifulSoup(r.text, 'html.parser')
    messages = []
    
    for item in soup.find_all('div', class_='list-item'):
        header_div = item.find('div', class_='list-item-header')
        content_div = item.find('div', class_='list-item-content')
        if not header_div or not content_div:
            continue
            
        # Get sender
        title_h3 = header_div.find('h3', class_='list-item-title')
        sender = title_h3.text.strip() if title_h3 else "Unknown"
        
        # Get date
        meta_span = header_div.find('span', class_='list-item-meta')
        date_text = meta_span.text.strip() if meta_span else "Unknown"
        
        # Get text
        text = content_div.text.strip()
        
        messages.append({
            'sender': sender,
            'time': date_text,
            'text': text
        })
        
    return messages

msgs = get_sms_messages('12018577757')
print(f"Total messages parsed: {len(msgs)}")
for i, m in enumerate(msgs[:5]):
    print(f"[{i+1}] Sender: {m['sender']} ({m['time']})")
    print(f"    Message: {m['text']}")
    print("-" * 50)
