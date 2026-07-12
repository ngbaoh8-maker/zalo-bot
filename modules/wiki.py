import requests
from zlapi.models import Message
import urllib.parse
import difflib
import logging
import threading
from config import PREFIX

# --- Cấu hình ---
logger = logging.getLogger(__name__)

des = {
    'version': "1.3.0",
    'credits': "ngbao",
    'description': "Tra cứu Wikipedia thông minh với cơ chế gợi ý chính xác",
    'power': "Thành Viên"
}

def clean_wiki_text(text):
    """Làm sạch văn bản từ Wikipedia để hiển thị đẹp hơn"""
    if not text: return ""
    # Giới hạn độ dài và xử lý các ký tự thừa nếu có
    text = text.strip()
    if len(text) > 1200:
        text = text[:1200] + "..."
    return text

def handle_wiki_command(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        msg = f"⚠️ Vui lòng nhập từ khóa!\nVí dụ: {PREFIX}wiki Trái Đất"
        return client.replyMessage(Message(text=msg), message_object, thread_id, thread_type)

    keyword = parts[1].strip()

    def search_process():
        try:
            client.sendReaction(message_object, "🔍", thread_id, thread_type)
            
            api_url = "https://vi.wikipedia.org/w/api.php"
            headers = {"User-Agent": "ZaloBotWiki/1.0 (contact: bot_admin)"}

            # 1. Tìm kiếm danh sách tiêu đề phù hợp
            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": keyword,
                "srlimit": 5
            }
            
            search_res = requests.get(api_url, params=search_params, headers=headers, timeout=10)
            search_data = search_res.json()
            search_results = search_data.get("query", {}).get("search", [])

            if not search_results:
                client.replyMessage(Message(text=f"❌ Không tìm thấy kết quả nào cho: {keyword}"), message_object, thread_id, thread_type)
                return

            # Tìm kết quả khớp nhất bằng difflib
            titles = [s['title'] for s in search_results]
            best_match = difflib.get_close_matches(keyword, titles, n=1, cutoff=0.1)
            final_title = best_match[0] if best_match else titles[0]

            # 2. Lấy nội dung chi tiết bài viết
            content_params = {
                "action": "query",
                "format": "json",
                "prop": "extracts|info",
                "exintro": True,
                "explaintext": True,
                "inprop": "url",
                "titles": final_title,
                "redirects": 1
            }

            content_res = requests.get(api_url, params=content_params, headers=headers, timeout=10)
            pages = content_res.json().get("query", {}).get("pages", {})
            page_id = list(pages.keys())[0]

            if page_id == "-1":
                client.replyMessage(Message(text="❌ Có lỗi khi truy xuất nội dung chi tiết."), message_object, thread_id, thread_type)
                return

            page_data = pages[page_id]
            title = page_data.get("title")
            extract = clean_wiki_text(page_data.get("extract", ""))
            full_url = page_data.get("fullurl", f"https://vi.wikipedia.org/wiki/{urllib.parse.quote(title)}")

            # 3. Gửi phản hồi
            response_text = (
                f"📚 [ WIKIPEDIA VIỆT NAM ] 📚\n"
                f"━━━━━━━━━━━━━━\n"
                f"🔍 Kết quả: {title}\n\n"
                f"{extract}\n"
                f"━━━━━━━━━━━━━━\n"
                f"🔗 Xem thêm: {full_url}"
            )
            
            client.replyMessage(Message(text=response_text), message_object, thread_id, thread_type)
            client.sendReaction(message_object, "✅", thread_id, thread_type)

        except Exception as e:
            logger.error(f"Lỗi Wiki: {e}")
            client.replyMessage(Message(text="⚠️ Hệ thống Wikipedia đang gặp sự cố kết nối."), message_object, thread_id, thread_type)

    # Chạy trong Thread để tránh treo Bot khi API phản hồi chậm
    threading.Thread(target=search_process, daemon=True).start()

def PTA():
    return {'wiki': handle_wiki_command}