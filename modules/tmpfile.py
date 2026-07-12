import requests
from zlapi.models import Message
import json
import os

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "UpLoad ảnh, video, voice lên tmpfiles.org",
    'power': "Thành viên"
}

TMPFILES_API_URL = 'https://tmpfiles.org/api/v1/upload'

def handle_upload_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        if hasattr(message_object, 'msgType') and message_object.msgType in ["chat.photo", "chat.video.msg", "chat.voice", "share.file"]:
            media_url = message_object.content.get('href', '').replace("\\/", "/")
            if not media_url:
                send_error_message("Không tìm thấy liên kết file.", thread_id, thread_type, client)
                return

            tmpfiles_link = upload_to_tmpfiles(media_url)
            if tmpfiles_link:
                send_success_message(f"Thành Công: {tmpfiles_link}", thread_id, thread_type, client)
            else:
                send_error_message("Lỗi khi upload file lên tmpfiles.org.", thread_id, thread_type, client)

        elif getattr(message_object, 'quote', None):
            attach = getattr(message_object.quote, 'attach', None)
            if attach:
                try:
                    attach_data = json.loads(attach)
                except json.JSONDecodeError:
                    send_error_message("Phân tích JSON thất bại.", thread_id, thread_type, client)
                    return

                media_url = attach_data.get('hdUrl') or attach_data.get('href')
                if media_url:
                    tmpfiles_link = upload_to_tmpfiles(media_url)
                    if tmpfiles_link:
                        send_success_message(f"File đã được upload: {tmpfiles_link}", thread_id, thread_type, client)
                    else:
                        send_error_message("Lỗi khi upload file lên tmpfiles.org.", thread_id, thread_type, client)
                else:
                    send_error_message("Không tìm thấy liên kết trong file đính kèm.", thread_id, thread_type, client)
            else:
                send_error_message("Không tìm thấy file đính kèm.", thread_id, thread_type, client)
        else:
            send_error_message("Vui lòng gửi file hoặc phản hồi file đính kèm.", thread_id, thread_type, client)
    except Exception as e:
        print(f"Lỗi khi xử lý lệnh upload: {str(e)}")
        send_error_message("Đã xảy ra lỗi khi xử lý lệnh.", thread_id, thread_type, client)


def upload_to_tmpfiles(media_url):
    try:
        response = requests.get(media_url, stream=True)
        response.raise_for_status()

        filename = os.path.basename(media_url)
        files = {'file': (filename, response.raw, response.headers.get('Content-Type'))}
        upload_response = requests.post(TMPFILES_API_URL, files=files)

        if upload_response.status_code == 200:
            return upload_response.text.strip()
        else:
            print(f"Lỗi API tmpfiles.org: {upload_response.status_code} - {upload_response.text}")
            return None
    except requests.RequestException as e:
        print(f"Lỗi khi gọi API tmpfiles.org: {str(e)}")
        return None
    except Exception as e:
        print(f"Lỗi không xác định: {str(e)}")
        return None


def send_success_message(message, thread_id, thread_type, client):
    success_message = Message(text=message)
    try:
        client.send(success_message, thread_id, thread_type)
    except Exception as e:
        print(f"Lỗi khi gửi tin nhắn thành công: {str(e)}")

def send_error_message(message, thread_id, thread_type, client):
    error_message = Message(text=message)
    try:
        client.send(error_message, thread_id, thread_type)
    except Exception as e:
        print(f"Lỗi khi gửi tin nhắn lỗi: {str(e)}")

def PTA():
    return {
        'tmpfile': handle_upload_command
    }