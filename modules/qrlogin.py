import os
import time
import json
import threading
import traceback
import re
import base64
import requests

from zlapi import ZaloAPI, ThreadType
from zlapi.models import Message
from zlapi._exception import ZaloLoginError
from config import ADMIN

des = {
    'version': "1.0.5",
    'credits': "ngbao",
    'description': "Tạo mã QR để đăng nhập Zalo, sau đó trả về thông tin session (cookie, imei).",
    'power': "Quản Trị Viên Bot"
}

DEFAULT_TTL = 120000 
QR_TTL = 100000

def login_and_get_session_info(client, thread_id, thread_type):
    temp_client = None
    qr_file_path = f"qr_login_{thread_id}_{int(time.time())}.png"

    try:
        temp_client = ZaloAPI(phone=None, password=None, imei=None, auto_login=False)
        
        client.send(
            Message(text="⏳ Đang khởi tạo phiên đăng nhập QR, vui lòng chờ..."),
            thread_id,
            thread_type,
            ttl=DEFAULT_TTL
        )
        
        def send_qr_to_user(path_to_qr):
            if os.path.exists(path_to_qr):
                instruction_message = Message(text="🪪 MÃ QR ĐĂNG NHẬP ZALO CỦA BẠN ĐÂY.\n✅️ QUÉT MÃ TRONG VÒNG 100 GIÂY ĐỂ ĐĂNG NHẬP BOT.")
                
                client.sendLocalImage(
                    imagePath=path_to_qr,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    message=instruction_message,
                    ttl=QR_TTL
                )
        
        temp_client.loginWithQR(
            qr_path=qr_file_path,
            on_qr_generated=send_qr_to_user
        )
        
        if temp_client.isLoggedIn():
            imei = temp_client._state.user_imei
            cookies = temp_client.getSession()
            
            cookies_str = json.dumps(cookies, indent=2, ensure_ascii=False)
            
            success_msg = (
                f"✅ Đăng nhập thành công!\n\n"
                f"🔑 IMEI:\n{imei}\n\n"
                f"🍪 Cookie (JSON):\n{cookies_str}\n\n"
                f"Lưu ý: Hãy bảo mật thông tin này cẩn thận!"
            )
            client.send(Message(text=success_msg), thread_id, thread_type, ttl=DEFAULT_TTL)

    except ZaloLoginError as e:
        if "Hết thời gian chờ quét mã QR" in str(e):
            error_msg = "⏰ Hết thời gian chờ. Không ai quét mã QR trong vòng 100 giây mã QR đã vô hiệu hóa."
        else:
            error_msg = f"❌ Đã xảy ra lỗi trong quá trình đăng nhập QR:\n\n{e}"
        
        client.send(Message(text=error_msg), thread_id, thread_type, ttl=DEFAULT_TTL)
        
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ Lỗi mạng trong quá trình đăng nhập QR:\n\n{e}"
        client.send(Message(text=error_msg), thread_id, thread_type, ttl=DEFAULT_TTL)
        
    except Exception as e:
        error_msg = f"❌ Đã xảy ra một lỗi không mong muốn:\n\n{e}"
        client.send(Message(text=error_msg), thread_id, thread_type, ttl=DEFAULT_TTL)
        traceback.print_exc()

    finally:
        if os.path.exists(qr_file_path):
            try:
                os.remove(qr_file_path)
            except OSError as e:
                print(f"Error removing file {qr_file_path}: {e}")

def handle_qrlogin_command(message, message_object, thread_id, thread_type, author_id, client):
    if str(author_id) not in ADMIN:
        msg = "🚦 Bạn không có quyền sử dụng lệnh này."
        client.send(Message(text=msg), thread_id, thread_type, ttl=DEFAULT_TTL)
        return

    login_thread = threading.Thread(
        target=login_and_get_session_info,
        args=(client, thread_id, thread_type)
    )
    login_thread.start()

def PTA():
    return {
        'qrlogin': handle_qrlogin_command
    }