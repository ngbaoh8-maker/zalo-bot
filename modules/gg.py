from zlapi.models import Message, ZaloAPIException, MultiMsgStyle, MessageStyle
from config import ADMIN, IMEI
import requests
from bs4 import BeautifulSoup

des = {
    'version': "1.0.1",
    'credits': "ngbao",
    'description': "Lệnh tìm kiếm thông tin trên Google",
    'power': "Thành Viên"
}

def handle_search_command(message, message_object, thread_id, thread_type, author_id, client):
    if author_id not in ADMIN:
        msg = "Bạn không có quyền sử dụng lệnh này!"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=10000, style="font", size="10", auto_format=False),
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
        return

    try:
        parts = message.split(" ", 1)
        if len(parts) < 2:
            msg = "Nhập từ khóa tìm kiếm!"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=10000, style="font", size="10", auto_format=False),
            ])
            client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
            return

        search_query = parts[1].strip()
        search_results = search_google(search_query)

        if search_results:
            formatted_results = "\n".join([f"{i+1}. {title} - {link}" for i, (title, link) in enumerate(search_results)])
            msg = f"Kết quả tìm kiếm cho '{search_query}':\n\n{formatted_results}"
        else:
            msg = f"Không tìm thấy kết quả cho '{search_query}'."
        
        styles = MultiMsgStyle([
             MessageStyle(offset=0, length=10000, style="font", size="10", auto_format=False),
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=120000)

    except Exception as e:
        msg = f"Lỗi không xác định: {e}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=10000, style="font", size="10", auto_format=False),
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=120000)

def search_google(query):
    url = f"https://www.google.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" 
    }
    try:
      response = requests.get(url, headers=headers)
      response.raise_for_status()
    except requests.exceptions.RequestException as e:
      print(f"Error during request: {e}")
      return None

    soup = BeautifulSoup(response.content, "html.parser")
    results = []
    for g in soup.find_all("div", class_="yuRUbf"):
        a_tag = g.find("a")
        if a_tag:
            title = a_tag.find("h3").text
            link = a_tag["href"]
            results.append((title, link))
    return results


def PTA():
    return {
        'gg': handle_search_command
    }