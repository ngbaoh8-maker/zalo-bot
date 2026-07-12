from zlapi import ZaloAPI
from zlapi.models import *
import time
from concurrent.futures import ThreadPoolExecutor
import threading
from deep_translator import GoogleTranslator

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Dịch ngôn ngữ",
    'power': "Thành viên"
}

def handle_translate_command(message, message_object, thread_id, thread_type, author_id, client):
    message_text = message_object.get('content', '').strip()
    parts = message_text.split(maxsplit=2)
    if len(parts) < 3:
        language_menu = """
        Vui lòng chọn ngôn ngữ đích để dịch. Các ngôn ngữ hỗ trợ:

        - en: Tiếng Anh
        - vi: Tiếng Việt
        - es: Tiếng Tây Ban Nha
        - fr: Tiếng Pháp
        - de: Tiếng Đức
        - ru: Tiếng Nga
        - ja: Tiếng Nhật
        - ko: Tiếng Hàn
        - zh: Tiếng Trung
        - it: Tiếng Ý

        Ví dụ: "dich ngbao dz cte!"
        """
        client.replyMessage(Message(text=language_menu), message_object, thread_id, thread_type)
        return
    target_language = parts[1]  
    text_to_translate = parts[2]  

    try:
        translated = GoogleTranslator(source='auto', target=target_language).translate(text_to_translate)
        response = f"Dịch từ '{text_to_translate}' sang '{target_language}': {translated}"
        client.replyMessage(Message(text=response), message_object, thread_id, thread_type)
    except Exception as e:
        client.replyMessage(Message(text=f"Lỗi khi dịch: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {
        'dich': handle_translate_command
    }
