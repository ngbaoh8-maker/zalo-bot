import json
import os
import logging
import requests
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle
from config import PREFIX

logger = logging.getLogger(__name__)

try:
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
    with open(path, 'r', encoding='utf-8') as f:
        settings = json.load(f)
    ADMIN_ID = settings['admin']
    ADM_IDS = settings['adm']
except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
    logging.error(f"Failed to load seting.json: {e}")
    ADMIN_ID = ""
    ADM_IDS = []

des = {
    'version': "1.0.7",
    'credits': "ngbao",
    'description': "Lưu trữ tin nhắn thoại và gửi.",
    'power': "Admin"
}

def get_user_name(client, uid):
    """Lấy tên user từ user_id."""
    try:
        user_info = client.fetchUserInfo(uid)
        author_info = user_info.changed_profiles.get(str(uid), {}) if user_info and user_info.changed_profiles else {}
        name = author_info.get('zaloName', 'Không xác định')
        return name
    except Exception as e:
        logger.error(f"[get_user_name] Failed to fetch name for user {uid}: {e}")
        return 'Không xác định'

def upload_to_host(file_name):
    """Upload file to uguu.se and return the URL."""
    try:
        with open(file_name, 'rb') as file:
            files = {'files[]': file}
            response = requests.post('https://uguu.se/upload', files=files).json()
            if response['success']:
                return response['files'][0]['url']
            return False
    except Exception as e:
        logger.error(f"[MSVC] Error in upload_to_host: {e}")
        return False

class MSVCHandler:
    def __init__(self, client, *args, **kwargs):
        self.client = client
        self.voices_file = "data/saved_voices.json"
        self.voices_dir = "data/voice"
        
        for directory in ["data", self.voices_dir]:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                    logger.info(f"[MSVC] Đã tạo thư mục '{directory}'.")
                except OSError as e:
                    logger.error(f"[MSVC] Không thể tạo thư mục '{directory}': {e}")
        
        self.saved_voices = self.load_saved_voices()

    def load_saved_voices(self):
        """Load saved voices metadata from JSON file."""
        try:
            if os.path.exists(self.voices_file):
                with open(self.voices_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
                    logger.warning(f"[MSVC] File {self.voices_file} không chứa định dạng dictionary. Khởi tạo danh sách rỗng.")
                    return {}
            return {}
        except json.JSONDecodeError:
            logger.error(f"[MSVC] Lỗi giải mã file {self.voices_file}. Khởi tạo danh sách rỗng.")
            return {}
        except Exception as e:
            logger.error(f"[MSVC] Lỗi khi tải dữ liệu voice từ {self.voices_file}: {e}")
            return {}

    def save_saved_voices(self):
        """Save voices metadata to JSON file."""
        try:
            with open(self.voices_file, "w", encoding="utf-8") as f:
                json.dump(self.saved_voices, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[MSVC] Lỗi khi lưu dữ liệu voice vào {self.voices_file}: {e}")

    def is_admin(self, author_id):
        """Check if the user is an admin."""
        return str(author_id) == str(ADMIN_ID) or str(author_id) in [str(id) for id in ADM_IDS]

    def download_voice(self, url, file_path):
        """Download voice file from URL and save as .aac."""
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"[MSVC] Đã tải và lưu voice vào {file_path}")
                return True
            else:
                logger.error(f"[MSVC] Không thể tải voice từ {url}. Mã trạng thái: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"[MSVC] Lỗi khi tải voice từ {url}: {e}")
            return False

    def handle_luuvc_command(self, message_text, message_object, thread_id, thread_type, author_id):
        """Handle 'luuvc' command (save voice as .aac, upload to host, and store URL)."""
        name = get_user_name(self.client, author_id)

        if not self.is_admin(author_id):
            rest_text = "❌ Lệnh này chỉ dành cho admin."
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
            return

        try:
            parts = message_text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                rest_text = f"Cách dùng: {PREFIX}luuvc <tên voice> (reply vào tin nhắn thoại)"
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "👉", thread_id, thread_type, reactionType=75)
                return

            voice_name = parts[1].strip()
            if voice_name in self.saved_voices:
                rest_text = f"Tên voice '{voice_name}' đã tồn tại. Vui lòng chọn tên khác."
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "⚠️", thread_id, thread_type, reactionType=75)
                return

            quote_data = getattr(message_object, 'quote', None)
            if not quote_data:
                rest_text = "➜ Bạn cần reply vào một tin nhắn thoại để lưu."
                msg = f"{name}\n{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "⚠️", thread_id, thread_type, reactionType=75)
                return

            replied_message_type_from_quote = quote_data.get('cliMsgType')
            expected_voice_types = [3, 31]

            if replied_message_type_from_quote not in expected_voice_types:
                rest_text = f"➜ Tin nhắn được reply không phải là tin nhắn thoại. Loại tin nhắn trong quote: {replied_message_type_from_quote}."
                msg = f"{name}\n{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
                return
            
            voice_url = None
            file_size = None
            replied_attach_str = quote_data.get('attach')
            try:
                if not isinstance(replied_attach_str, str) or not replied_attach_str.strip():
                    logger.error(f"[MSVC] Trường 'attach' trong quote_data không phải chuỗi hợp lệ hoặc rỗng: '{replied_attach_str}'")
                    raise ValueError("Dữ liệu đính kèm ('attach') của tin nhắn thoại được reply không hợp lệ hoặc trống.")

                replied_voice_content = json.loads(replied_attach_str)
                voice_url = replied_voice_content.get("href") or replied_voice_content.get("voiceUrl") or replied_voice_content.get("m4aUrl")

                params_data_str = replied_voice_content.get("params")
                if isinstance(params_data_str, str):
                    try:
                        params_inner_dict = json.loads(params_data_str)
                        file_size = params_inner_dict.get("size") or params_inner_dict.get("fileSize")
                    except json.JSONDecodeError:
                        logger.warning(f"[MSVC] Không thể phân tích JSON 'params' lồng nhau trong replied_voice_content: {params_data_str}")
                
                if file_size is None:
                    file_size = replied_voice_content.get("size") or replied_voice_content.get("fileSize")

                if file_size is not None:
                    try:
                        file_size = int(file_size)
                    except (ValueError, TypeError):
                        logger.warning(f"[MSVC] fileSize '{file_size}' từ replied_voice_content không phải số nguyên hợp lệ. Đặt thành None.")
                        file_size = None

                if not voice_url:
                    logger.error(f"[MSVC] Không thể trích xuất voice_url từ replied_voice_content: {replied_voice_content}")
                    raise ValueError("Không thể trích xuất URL của tin nhắn thoại từ quote.attach.")

            except (json.JSONDecodeError, TypeError, AttributeError, ValueError) as e:
                logger.error(f"[MSVC] Lỗi khi xử lý 'attach' từ quote_data cho luuvc: {e}. Chuỗi attach trong quote là: '{replied_attach_str}'")
                rest_text = f"➜ Lỗi xử lý nội dung thoại được reply từ quote: {str(e)}."
                msg = f"{name}\n{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
                return

            file_name = f"{voice_name}_{author_id}_{thread_id}.aac"
            file_path = os.path.join(self.voices_dir, file_name)

            if not self.download_voice(voice_url, file_path):
                rest_text = "❌ Lỗi khi tải voice từ URL. Vui lòng thử lại."
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
                return

            uploaded_url = upload_to_host(file_path)
            if not uploaded_url:
                rest_text = "❌ Lỗi khi tải voice lên host. Vui lòng thử lại."
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
                try:
                    os.remove(file_path)
                    logger.info(f"[MSVC] Đã xóa file tạm thời {file_path} sau khi upload thất bại.")
                except OSError as e:
                    logger.error(f"[MSVC] Lỗi khi xóa file tạm thời {file_path}: {e}")
                return

            self.saved_voices[voice_name] = {
                "url": uploaded_url,
                "file_path": file_path,
                "fileSize": file_size
            }
            self.save_saved_voices()

            rest_text = f"✅ Đã lưu voice với tên: {voice_name}"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "👍", thread_id, thread_type, reactionType=75)

        except Exception as e:
            logger.exception(f"[MSVC] Lỗi không xác định trong handle_luuvc_command:")
            rest_text = "❌ Lỗi khi lưu voice: Đã xảy ra lỗi không mong muốn."
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)

    def handle_svc_command(self, message_text, message_object, thread_id, thread_type, author_id):
        """Handle 'svc' command (upload .aac file to host and send using new URL)."""
        name = get_user_name(self.client, author_id)

        if not self.is_admin(author_id):
            rest_text = "❌ Lệnh này chỉ dành cho admin."
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
            return

        try:
            parts = message_text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                rest_text = f"➜ Cách dùng: {PREFIX}svc <tên voice>"
                msg = f"{name}\n{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "👉", thread_id, thread_type, reactionType=75)
                return

            voice_name = parts[1].strip()
            if voice_name not in self.saved_voices:
                rest_text = f"➜ Không tìm thấy voice với tên: {voice_name}"
                msg = f"{name}\n{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "⚠️", thread_id, thread_type, reactionType=75)
                return

            voice_data = self.saved_voices[voice_name]
            file_path = voice_data.get("file_path")
            file_size = voice_data.get("fileSize")

            if not file_path or not os.path.exists(file_path):
                logger.error(f"[MSVC] File voice {file_path} không tồn tại.")
                rest_text = f"❌ File voice '{voice_name}' không tồn tại trên hệ thống."
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
                return

            voice_url = upload_to_host(file_path)
            if not voice_url:
                logger.error(f"[MSVC] Không thể tải file voice {file_path} lên host.")
                rest_text = f"❌ Lỗi khi tải voice '{voice_name}' lên host."
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
                return

            rest_text = f"🔊 Gửi voice: {voice_name}"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.sendMessage(
                Message(text=msg, style=styles),
                thread_id, thread_type, ttl=30000
            )
            self.client.sendReaction(message_object, "🎤", thread_id, thread_type, reactionType=75)

            self.client.sendRemoteVoice(
                voiceUrl=voice_url,
                thread_id=thread_id,
                thread_type=thread_type,
                fileSize=file_size,
                ttl=120000
            )

        except Exception as e:
            logger.exception(f"[MSVC] Lỗi không xác định trong handle_svc_command:")
            rest_text = "❌ Lỗi khi gửi voice: Đã xảy ra lỗi không mong muốn."
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)

    def handle_listvoice_command(self, message_text, message_object, thread_id, thread_type, author_id):
        """Handle 'listvoice' command (list saved voices)."""
        name = get_user_name(self.client, author_id)

        if not self.is_admin(author_id):
            rest_text = "❌ Lệnh này chỉ dành cho admin."
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
            return

        try:
            if not self.saved_voices:
                rest_text = "➜ Chưa có voice nào được lưu."
                msg = f"{name}\n{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "⚠️", thread_id, thread_type, reactionType=75)
                return

            voice_names = list(self.saved_voices.keys())
            if not voice_names:
                rest_text = "➜ Chưa có voice nào được lưu (danh sách trống)."
                msg = f"{name}\n{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "⚠️", thread_id, thread_type, reactionType=75)
                return

            header = "🎤 Danh sách voice đã lưu:\n"
            max_msg_len = 3800
            lines_to_send = [f"{i}. {name}" for i, name in enumerate(voice_names, 1)]
            current_message_content = header
            first_chunk = True

            for line in lines_to_send:
                if len(current_message_content) + len(line) + 1 > max_msg_len:
                    msg = f"{name}\n➜{current_message_content.strip()}"
                    styles = MultiMsgStyle([
                        MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                        MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                    ])
                    self.client.replyMessage(
                        Message(text=msg, style=styles),
                        message_object, thread_id, thread_type, ttl=120000
                    )
                    self.client.sendReaction(message_object, "🔍", thread_id, thread_type, reactionType=75)
                    current_message_content = ""
                    first_chunk = False

                current_message_content += line + "\n"

            if current_message_content.strip():
                if not first_chunk and current_message_content.strip() == header.strip():
                    pass
                else:
                    msg = f"{name}\n➜{current_message_content.strip()}"
                    styles = MultiMsgStyle([
                        MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                        MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                    ])
                    self.client.replyMessage(
                        Message(text=msg, style=styles),
                        message_object, thread_id, thread_type, ttl=120000
                    )
                    self.client.sendReaction(message_object, "🔍", thread_id, thread_type, reactionType=75)

        except Exception as e:
            logger.exception(f"[MSVC] Lỗi không xác định trong handle_listvoice_command:")
            rest_text = "❌ Lỗi khi liệt kê voice: Đã xảy ra lỗi không mong muốn."
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)

    def handle_delvc_command(self, message_text, message_object, thread_id, thread_type, author_id):
        """Handle 'delvc' command (delete saved voice and .aac file)."""
        name = get_user_name(self.client, author_id)

        if not self.is_admin(author_id):
            rest_text = "❌ Lệnh này chỉ dành cho admin."
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
            return

        try:
            parts = message_text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                rest_text = f"➜ Cách dùng: {PREFIX}delvc <tên voice>"
                msg = f"{name}\n{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "👉", thread_id, thread_type, reactionType=75)
                return

            voice_name = parts[1].strip()
            if voice_name not in self.saved_voices:
                rest_text = f"➜ Không tìm thấy voice với tên: {voice_name}"
                msg = f"{name}\n{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "⚠️", thread_id, thread_type, reactionType=75)
                return

            voice_data = self.saved_voices[voice_name]
            file_path = voice_data.get("file_path")

            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"[MSVC] Đã xóa file voice {file_path}")
                except OSError as e:
                    logger.error(f"[MSVC] Lỗi khi xóa file voice {file_path}: {e}")
                    rest_text = f"❌ Lỗi khi xóa file voice '{voice_name}': {str(e)}"
                    msg = f"{name}\n➜{rest_text}"
                    styles = MultiMsgStyle([
                        MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                        MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                    ])
                    self.client.replyMessage(
                        Message(text=msg, style=styles),
                        message_object, thread_id, thread_type, ttl=60000
                    )
                    self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
                    return

            del self.saved_voices[voice_name]
            self.save_saved_voices()

            rest_text = f"✅ Đã xóa voice với tên: {voice_name}"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "🗑️", thread_id, thread_type, reactionType=75)

        except Exception as e:
            logger.exception(f"[MSVC] Lỗi không xác định trong handle_delvc_command:")
            rest_text = "❌ Lỗi khi xóa voice: Đã xảy ra lỗi không mong muốn."
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#15a85f", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)