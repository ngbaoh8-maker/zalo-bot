import sys, requests, re, random
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# ============ TEST 1: Lấy số VN từ sms24.me ============
print("=" * 60)
print("[TEST 1] Lấy danh sách số VN từ sms24.me...")
try:
    r = requests.get('https://sms24.me/en/countries/vn', headers=HEADERS, timeout=15)
    print(f"  Status: {r.status_code}")
    soup = BeautifulSoup(r.text, 'html.parser')
    numbers = []
    for a in soup.find_all('a'):
        href = a.get('href', '')
        if '/numbers/' in href:
            num = href.rstrip('/').split('/')[-1]
            if num.startswith('84') and num.isdigit():
                numbers.append(num)
    numbers = list(set(numbers))
    print(f"  Tìm thấy: {len(numbers)} số VN")
    if numbers:
        print(f"  Ví dụ: {numbers[:5]}")
except Exception as e:
    print(f"  LỖI: {e}")
    numbers = []

# ============ TEST 2: Đọc tin nhắn từ sms24.me ============
if numbers:
    test_phone = random.choice(numbers)
    print(f"\n{'=' * 60}")
    print(f"[TEST 2] Đọc tin nhắn cho số +{test_phone} từ sms24.me...")
    try:
        url = f"https://sms24.me/en/numbers/{test_phone}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        print(f"  Status: {r.status_code}")
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # In ra 5 thẻ HTML đầu tiên để debug cấu trúc
        print(f"\n  --- DEBUG: Tìm <table> ---")
        tables = soup.find_all('table')
        print(f"  Số bảng: {len(tables)}")
        
        # Thử tìm bằng nhiều cách
        print(f"\n  --- DEBUG: Tìm các class phổ biến ---")
        for cls_name in ['message', 'sms', 'msg', 'item', 'card', 'row', 'entry']:
            found = soup.find_all(class_=re.compile(cls_name, re.IGNORECASE))
            if found:
                print(f"  class chứa '{cls_name}': {len(found)} phần tử")
                # In HTML của phần tử đầu tiên
                print(f"    Mẫu: {str(found[0])[:200]}")
        
        # In toàn bộ body text nếu cần
        body = soup.find('body')
        if body:
            all_text = body.get_text(separator='|', strip=True)
            # Tìm đoạn có dấu hiệu tin nhắn
            segments = [s for s in all_text.split('|') if len(s) > 20]
            print(f"\n  --- DEBUG: {len(segments)} đoạn text dài > 20 ký tự ---")
            for s in segments[:10]:
                print(f"    → {s[:100]}")
                
        # Thử tìm bằng data-* attributes
        print(f"\n  --- DEBUG: Tìm thẻ có data-* ---")
        for tag in soup.find_all(attrs={"data-message": True}):
            print(f"  data-message: {tag.text[:100]}")
        for tag in soup.find_all(attrs={"data-content": True}):
            print(f"  data-content: {tag.text[:100]}")

        # In raw HTML 2000-4000 ký tự (vùng body)
        html_text = r.text
        body_start = html_text.find('<body')
        if body_start > 0:
            snippet = html_text[body_start:body_start+3000]
            print(f"\n  --- RAW HTML (body, 3000 chars) ---")
            print(snippet[:3000])
            
    except Exception as e:
        print(f"  LỖI: {e}")
        import traceback
        traceback.print_exc()

# ============ TEST 3: Đọc tin nhắn từ sms-online.co ============
print(f"\n{'=' * 60}")
print("[TEST 3] Đọc tin nhắn từ sms-online.co...")
try:
    r = requests.get('https://sms-online.co/receive-free-sms/12018577757', headers=HEADERS, timeout=15)
    print(f"  Status: {r.status_code}")
    soup = BeautifulSoup(r.text, 'html.parser')
    msgs = []
    for item in soup.find_all('div', class_='list-item'):
        header_div = item.find('div', class_='list-item-header')
        content_div = item.find('div', class_='list-item-content')
        if not header_div or not content_div:
            continue
        title_h3 = header_div.find('h3', class_='list-item-title')
        sender = title_h3.text.strip() if title_h3 else "?"
        text = content_div.text.strip()
        msgs.append({'sender': sender, 'text': text})
    print(f"  Tin nhắn: {len(msgs)}")
    for m in msgs[:3]:
        print(f"    [{m['sender']}] {m['text'][:80]}")
except Exception as e:
    print(f"  LỖI: {e}")

print(f"\n{'=' * 60}")
print("DONE!")
