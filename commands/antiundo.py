import json
import os
import time
import re
import queue
import unicodedata
import collections
from datetime import datetime, timedelta
import threading
import requests
from PIL import Image
from zlapi.models import Message, MultiMsgStyle, MessageStyle, Mention, ThreadType 
from logging_utils import Logging
from config import PREFIX, ADMIN

logger = Logging()

class UndoHandler:
    def __init__(self, client):
        self.client = client
        self.FileNM = 'database/dataundo.json'
        self.undo_cache_maxlen = 1000
        self.undo_cache = collections.deque(maxlen=self.undo_cache_maxlen)
        self.undo_cache_lock = threading.Lock()
        self.undo_write_queue = queue.Queue()
        self.undo_flush_interval = 5

        self._load_initial_undo_cache()
        self.undo_writer_thread = threading.Thread(target=self._undo_writer_process, daemon=True)
        self.undo_writer_thread.start()
        self.undo_enabled = self.load_undo_settings()
        self.last_undo_reset = self.load_last_undo_reset()
        self.check_and_reset_undo()
        self._ensure_undo_file_exists()

    def _ensure_undo_file_exists(self):
        if not os.path.exists(self.FileNM):
            try:
                with open(self.FileNM, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                logger.info(f"[AntiUndo] Created empty {self.FileNM} for undo data.")
            except Exception as e:
                logger.error(f"[AntiUndo] Could not create empty {self.FileNM}: {e}")
        else:
            try:
                with open(self.FileNM, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        logger.warning(f"[AntiUndo] {self.FileNM} is not a JSON list. Resetting file.")
                        with open(self.FileNM, 'w', encoding='utf-8') as f_reset:
                            json.dump([], f_reset)
            except json.JSONDecodeError:
                logger.warning(f"[AntiUndo] {self.FileNM} is corrupted. Resetting file.")
                with open(self.FileNM, 'w', encoding='utf-8') as f_reset:
                    json.dump([], f_reset)
            except Exception as e:
                logger.error(f"[AntiUndo] Error checking {self.FileNM} integrity: {e}")


    def _load_initial_undo_cache(self):
        try:
            if os.path.exists(self.FileNM):
                with open(self.FileNM, 'r', encoding='utf-8') as f:
                    all_messages = json.load(f)
                    with self.undo_cache_lock:
                        for msg in all_messages[-self.undo_cache_maxlen:]:
                            self.undo_cache.append(msg)
            logger.info(f"[AntiUndo] Loaded {len(self.undo_cache)} messages into undo cache from {self.FileNM}.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"[AntiUndo] Error loading initial undo cache from {self.FileNM}: {e}. Re-initializing file.")
            with open(self.FileNM, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _undo_writer_process(self):
        last_flush_time = time.time()
        messages_in_batch = []
        while True:
            try:
                message = self.undo_write_queue.get(timeout=0.1)
                messages_in_batch.append(message)
            except queue.Empty:
                pass

            current_time = time.time()
            if messages_in_batch and \
               (current_time - last_flush_time >= self.undo_flush_interval or \
                len(messages_in_batch) >= self.undo_cache_maxlen / 10):

                try:
                    with self.undo_cache_lock:
                        data_to_save = list(self.undo_cache)
                    
                    with open(self.FileNM, 'w', encoding='utf-8') as f:
                        json.dump(data_to_save, f, indent=4, ensure_ascii=False)
                    
                    logger.debug(f"[AntiUndo] Flushed {len(messages_in_batch)} undo messages to {self.FileNM}. Total cached: {len(data_to_save)}")
                    messages_in_batch = []
                    last_flush_time = current_time
                except Exception as e:
                    logger.error(f"[AntiUndo] Error flushing undo messages to file: {e}")
            time.sleep(0.01)

    def is_admin(self, author_id):
        return str(author_id) == str(ADMIN) or str(author_id) in [str(uid) for uid in ADM]

    def handle_undo_command(self, message_text, message_object, thread_id, thread_type, author_id):
        if not self.is_admin(author_id):
            user_info = self.client.fetchUserInfo(author_id)
            author_display_name = user_info.changed_profiles.get(str(author_id), {}).get('zaloName', 'Không xác định') if user_info and user_info.changed_profiles else str(author_id)
            
            rest_text = "Ủa bạn mình ơi, lệnh này chỉ admin xài thôi nha! 🥺"
            msg = f"{author_display_name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(author_display_name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(author_display_name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object,
                thread_id=thread_id,
                thread_type=thread_type,
                ttl=30000
            )
            self.client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
            return

        parts = message_text.lower().split()
        if len(parts) < 2:
            user_info = self.client.fetchUserInfo(author_id)
            author_display_name = user_info.changed_profiles.get(str(author_id), {}).get('zaloName', 'Không xác định') if user_info and user_info.changed_profiles else str(author_id)
            
            rest_text = f"Sai cú pháp rồi! Dùng {PREFIX}antiundo on/off/rs nha bro! 😉"
            msg = f"{author_display_name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(author_display_name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(author_display_name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object,
                thread_id=thread_id,
                thread_type=thread_type,
                ttl=30000
            )
            self.client.sendReaction(message_object, "👉", thread_id, thread_type, reactionType=75)
            return

        user_info = self.client.fetchUserInfo(author_id)
        author_display_name = user_info.changed_profiles.get(str(author_id), {}).get('zaloName', 'Không xác định') if user_info and user_info.changed_profiles else str(author_id)

        action = parts[1]
        current_state = self.undo_enabled.get("groups", {}).get(thread_id, False)

        if action == 'on':
            if current_state:
                rest_text = "Chế độ hóng hớt tin nhắn thu hồi đã bật sẵn rồi mà! 👀"
                msg = f"{author_display_name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(author_display_name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(author_display_name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ttl=30000
                )
                self.client.sendReaction(message_object, "🔄", thread_id, thread_type, reactionType=75)
            else:
                if "groups" not in self.undo_enabled:
                    self.undo_enabled["groups"] = {}
                self.undo_enabled["groups"][thread_id] = True
                self.save_undo_settings()
                rest_text = " đã bật chế độ hóng hớt tin nhắn thu hồi rồi đó! 👀"
                msg = f"{author_display_name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(author_display_name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(author_display_name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ttl=30000
                )
                self.client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
        elif action == 'off':
            if not current_state:
                rest_text = "Chế độ hóng hớt tin nhắn thu hồi đã tắt sẵn rồi! 😌"
                msg = f"{author_display_name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(author_display_name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(author_display_name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ttl=30000
                )
                self.client.sendReaction(message_object, "🔄", thread_id, thread_type, reactionType=75)
            else:
                if "groups" not in self.undo_enabled:
                    self.undo_enabled["groups"] = {}
                self.undo_enabled["groups"][thread_id] = False
                self.save_undo_settings()
                rest_text = " đã tắt chế độ soi mói tin nhắn thu hồi rồi đó! 😌"
                msg = f"{author_display_name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(author_display_name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(author_display_name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ttl=30000
                )
                self.client.sendReaction(message_object, "💨", thread_id, thread_type, reactionType=75)
        elif action == 'rs':
            try:
                self.reset_undo_data()
                rest_text = " đã reset sạch sẽ file dataundo.json rồi đó! ✨"
                msg = f"{author_display_name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(author_display_name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(author_display_name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ttl=30000
                )
                self.client.sendReaction(message_object, "🔄", thread_id, thread_type, reactionType=75)
            except Exception as e:
                logger.error(f"[AntiUndo] Error resetting dataundo.json: {e}")
                rest_text = f"Ui cha, có lỗi sảy ra khi reset file: {e} 😥"
                msg = f"{author_display_name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(author_display_name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(author_display_name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ttl=30000
                )
                self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
        else:
            user_info = self.client.fetchUserInfo(author_id)
            author_display_name = user_info.changed_profiles.get(str(author_id), {}).get('zaloName', 'Không xác định') if user_info and user_info.changed_profiles else str(author_id)
            
            rest_text = f"Sai cú pháp rồi! Dùng {PREFIX}antiundo on/off/rs nha bro! 😉"
            msg = f"{author_display_name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(author_display_name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(author_display_name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object,
                thread_id=thread_id,
                thread_type=thread_type,
                ttl=30000
            )
            self.client.sendReaction(message_object, "👉", thread_id, thread_type, reactionType=75)

    def load_undo_settings(self):
        try:
            with open("data/undo_settings.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"groups": {}}
        except json.JSONDecodeError:
            logger.error("[AntiUndo] Lỗi khi đọc file undo_settings.json. Khởi tạo settings mặc định.")
            return {"groups": {}}

    def save_undo_settings(self):
        try:
            with open("data/undo_settings.json", "w") as f:
                json.dump(self.undo_enabled, f, indent=4)
        except Exception as e:
            logger.error(f"[AntiUndo] Lỗi khi lưu cài đặt undo: {e}")

    def LuuNoiDungThuHoi(self, message_object, message_text):
        noidung_1 = self.message_object_undo(message_object, message_text)
        with self.undo_cache_lock:
            self.undo_cache.append(noidung_1)
        try:
            self.undo_write_queue.put_nowait(noidung_1)
        except queue.Full:
            logger.warning("[AntiUndo] Undo write queue is full, dropping message. Consider increasing queue size or flush interval.")

    def message_object_undo(self, message_object, message_text):
    
        stored_data = {
            'msgId': message_object.get('msgId'),
            'uidFrom': message_object.get('uidFrom') or message_object.get('userId'),
            'cliMsgId': message_object.get('cliMsgId'),
            'msgType': message_object.get('msgType'),
            'text': message_text,
            'content': {},
            'params': message_object.get('params')
        }

        content_dict = message_object.get('content')
        attach_dict = message_object.get('attach')
        
        source_dict = content_dict if isinstance(content_dict, dict) else attach_dict

        if isinstance(source_dict, dict):
            stored_data['content'] = {
                'href': source_dict.get('href'),
                'thumb': source_dict.get('thumb'),
                'params': source_dict.get('params'),
                'id': source_dict.get('id'),
                'catId': source_dict.get('catId')
            }
        
        if not stored_data['content'] and isinstance(message_object, Message):
             if isinstance(message_object.content, dict):
                 stored_data['content'] = message_object.content

        return stored_data

    def load_last_undo_reset(self):
        try:
            with open("data/undo_reset.json", "r") as f:
                data = json.load(f)
                return datetime.fromisoformat(data.get('last_reset', datetime.min.isoformat()))
        except (FileNotFoundError, json.JSONDecodeError):
            return datetime.min

    def save_last_undo_reset(self, last_reset_time):
        try:
            with open("data/undo_reset.json", "w") as f:
                json.dump({"last_reset": last_reset_time.isoformat()}, f, indent=4)
        except Exception as e:
            logger.error(f"[AntiUndo] Lỗi khi lưu thời gian reset undo: {e}")

    def check_and_reset_undo(self):
        now = datetime.now()
        if (now - self.last_undo_reset) >= timedelta(days=1):
            self.reset_undo_data()
            self.last_undo_reset = now
            self.save_last_undo_reset(now)

    def reset_undo_data(self):
        try:
            with open(self.FileNM, 'w') as f:
                json.dump([], f)
            with self.undo_cache_lock:
                self.undo_cache.clear()
            logger.info("[AntiUndo] Đã xóa nội dung file dataundo.json và cache.")
        except Exception as e:
            logger.error(f"[AntiUndo] Lỗi khi xóa nội dung file dataundo.json: {e}")

    def TimTinNhanThuHoi(self, cliMsgId):
        cliMsgId_str = str(cliMsgId)
        with self.undo_cache_lock:
            for msg in reversed(self.undo_cache):
                if str(msg.get('cliMsgId')) == cliMsgId_str:
                    return msg.get('id'), msg.get('catId')
        
        try:
            with open(self.FileNM, 'r', encoding='utf-8') as f:
                messages_from_file = json.load(f)
            for message in reversed(messages_from_file):
                if str(message.get('cliMsgId')) == cliMsgId_str:
                    return message.get('id'), message.get('catId')
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"[AntiUndo] Error reading undo file for TimTinNhanThuHoi (fallback): {e}")
        return None, None

    def Anhthuhoi(self, cliMsgId):
        cliMsgId_str = str(cliMsgId)
        with self.undo_cache_lock:
            for msg in reversed(self.undo_cache):
                if str(msg.get('cliMsgId')) == cliMsgId_str:
                    return msg.get('content')
        
        try:
            with open(self.FileNM, 'r', encoding='utf-8') as f:
                messages_from_file = json.load(f)
            for message in reversed(messages_from_file):
                if str(message.get('cliMsgId')) == cliMsgId_str:
                    return message.get('content')
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"[AntiUndo] Error reading undo file for Anhthuhoi (fallback): {e}")
        return None

    def DownAnhThuHoi(self, media_url, anh='undo.jpg'):
        try:
            response = requests.get(media_url)
            response.raise_for_status()
            with open(anh, 'wb') as f:
                f.write(response.content)
            return anh
        except requests.exceptions.RequestException as e:
            logger.error(f"[AntiUndo] Lỗi khi tải ảnh thu hồi: {e}")
            return None

    def _send_sticker_reconstruction(self, id, catId, thread_id, thread_type, author_id, message_object):
        try:
            author_info_for_sticker = self.client.fetchUserInfo(author_id)
            if author_info_for_sticker and getattr(author_info_for_sticker, "changed_profiles", None):
                fetched_name = author_info_for_sticker.changed_profiles.get(author_id, {}).get('zaloName')
                author_display_name_sticker = fetched_name if fetched_name and fetched_name != 'không xác định' else str(author_id)
            else:
                author_display_name_sticker = str(author_id)

            text = f"➜ [UNDO STICKER] {author_display_name_sticker} vừa thu hồi một sticker."
            styles = MultiMsgStyle([
                MessageStyle(offset=len("➜ "), length=len("[UNDO STICKER]"), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=len("➜ "), length=len("[UNDO STICKER]"), style="bold", auto_format=False),
            ])
            offset = text.find(f"{author_display_name_sticker}")
            self.client.replyMessage(Message(text=text, mention=Mention(author_id, len(f"{author_display_name_sticker}"), offset), style=styles), message_object, thread_id, thread_type, ttl=120000)
            self.client.sendSticker(1, id, catId, thread_id, thread_type)
        except Exception as e:
            logger.error(f"[AntiUndo] Lỗi khi gửi sticker: {e}")

    def is_undo_enabled(self, thread_id):
        if thread_id in self.undo_enabled.get("groups", {}):
            return self.undo_enabled["groups"][thread_id]
        return False

    def load_message_history(self):
        try:
            with open(self.FileNM, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as e:
            logger.error(f"[AntiUndo] Lỗi đọc lịch sử tin nhắn: {e}")
            return []

    def handle_undo_event(self, message_object, thread_id, thread_type, author_id):
        if not self.is_undo_enabled(thread_id):
            return

        cliMsgId_recalled = str(message_object.get('content', {}).get('cliMsgId'))
        if not cliMsgId_recalled:
            logger.warning(f"[AntiUndo] Không tìm thấy cliMsgId trong tin nhắn thu hồi. Bỏ qua.")
            return

        original_message = None
        with self.undo_cache_lock:
            for msg in reversed(self.undo_cache):
                if str(msg.get('cliMsgId')) == cliMsgId_recalled:
                    original_message = msg
                    break
        
        if not original_message:
            history = self.load_message_history()
            for msg in reversed(history):
                if str(msg.get('cliMsgId')) == cliMsgId_recalled:
                    original_message = msg
                    break

        if not original_message:
            logger.warning(f"[AntiUndo] Không tìm thấy thông tin cho cliMsgId {cliMsgId_recalled} trong cache và file.")
            return

        author_display_name = "Không rõ"
        user_info_display = self.client.fetchUserInfo(author_id)
        if user_info_display and getattr(user_info_display, "changed_profiles", None):
            fetched_name = user_info_display.changed_profiles.get(author_id, {}).get('zaloName')
            author_display_name = fetched_name if fetched_name and fetched_name != 'không xác định' else str(author_id)
        
        original_msg_type = original_message.get('msgType', '')
        original_content = original_message.get('content', {})
        original_text = original_message.get('text', '')

        is_video = False
        if original_msg_type.startswith('chat.video'): is_video = True
        elif isinstance(original_content.get('params'), str):
            try:
                params_data = json.loads(original_content['params'])
                if 'video_width' in params_data and 'duration' in params_data: is_video = True
            except: pass
        
        if is_video and original_content.get('href'):
            try:
                video_url = original_content['href']
                thumb_url = original_content.get('thumb')
                params_data = json.loads(original_content.get('params', '{}'))
                duration = params_data.get('duration', 0)
                width = params_data.get('video_width', 0)
                height = params_data.get('video_height', 0)
                
                text = f"➜ [UNDO VIDEO]\n{author_display_name} vừa thu hồi một video."
                styles = MultiMsgStyle([MessageStyle(offset=len("➜ "), length=len("[UNDO VIDEO]"), style="color", color="#db342e", auto_format=False), MessageStyle(offset=len("➜ "), length=len("[UNDO VIDEO]"), style="bold", auto_format=False)])
                self.client.replyMessage(Message(text=text, mention=Mention(author_id, len(author_display_name), text.find(author_display_name)), style=styles), message_object, thread_id, thread_type, ttl=120000)
                self.client.sendRemoteVideo(videoUrl=video_url, thumbnailUrl=thumb_url, duration=duration, width=width, height=height, thread_id=thread_id, thread_type=thread_type, ttl=120000)
                return
            except Exception as e: logger.error(f"[AntiUndo] Lỗi khi gửi lại video thu hồi: {e}")

        if original_msg_type.startswith('chat.voice') or (original_content.get('href') and '.aac' in original_content.get('href', '')):
            try:
                voice_url = original_content['href']
                fileSize = None
                if original_content.get('params') and isinstance(original_content['params'], str):
                    try:
                        params_dict = json.loads(original_content['params'])
                        fileSize = params_dict.get('fileSize')
                    except json.JSONDecodeError:
                        pass
                
                text = f"➜ [UNDO VOICE]\n{author_display_name} vừa thu hồi một tin nhắn thoại."
                styles = MultiMsgStyle([MessageStyle(offset=len("➜ "), length=len("[UNDO VOICE]"), style="color", color="#db342e", auto_format=False), MessageStyle(offset=len("➜ "), length=len("[UNDO VOICE]"), style="bold", auto_format=False)])
                self.client.replyMessage(Message(text=text, mention=Mention(author_id, len(author_display_name), text.find(author_display_name)), style=styles), message_object, thread_id, thread_type, ttl=120000)
                self.client.sendRemoteVoice(voice_url, thread_id, thread_type, ttl=120000, fileSize=fileSize)
                return
            except Exception as e: logger.error(f"[AntiUndo] Lỗi khi gửi voice thu hồi: {e}")

        if original_msg_type == 'share.file':
            try:
                file_url = original_content.get('href')
                file_name = "Tệp không tên"
                file_extension = None
                
                if original_text and "title='" in original_text:
                    match = re.search(r"title='([^']*)'", original_text)
                    if match: file_name = match.group(1)
                
                if isinstance(original_content.get('params'), str):
                    params_match_ext = re.search(r'"fileExt":"([^"]*)"', original_content['params'])
                    if params_match_ext: file_extension = params_match_ext.group(1)
                    
                    params_match_name = re.search(r'"fileName":"([^"]*)"', original_content['params'])
                    if params_match_name: file_name = params_match_name.group(1)


                text = f"➜ [UNDO TỆP]\n{author_display_name} vừa thu hồi một tệp tin."
                if file_name: 
                    text += f"\n➜ Tên tệp gốc: '{file_name}{('.' + file_extension) if file_extension else ''}'"

                styles = MultiMsgStyle([MessageStyle(offset=len("➜ "), length=len("[UNDO TỆP]"), style="color", color="#db342e", auto_format=False), MessageStyle(offset=len("➜ "), length=len("[UNDO TỆP]"), style="bold", auto_format=False)])
                self.client.replyMessage(Message(text=text, mention=Mention(author_id, len(author_display_name), text.find(author_display_name)), style=styles), message_object, thread_id, thread_type, ttl=120000)
                self.client.sendRemoteFile(fileUrl=file_url, fileName=file_name, extension=file_extension, thread_id=thread_id, thread_type=thread_type, ttl=120000)
                return
            except Exception as e: logger.error(f"[AntiUndo] Lỗi khi gửi lại file thu hồi: {e}")

        if original_msg_type.startswith('chat.photo') and original_content.get('href'):
            try:
                img_url = original_content['href']
                anh_path = self.DownAnhThuHoi(img_url)
                if anh_path:
                    image = Image.open(anh_path)
                    width, height = image.size
                    text = f"➜ [UNDO ẢNH]\n{author_display_name} vừa thu hồi một ảnh."
                    styles = MultiMsgStyle([MessageStyle(offset=len("➜ "), length=len("[UNDO ẢNH]"), style="color", color="#db342e", auto_format=False), MessageStyle(offset=len("➜ "), length=len("[UNDO ẢNH]"), style="bold", auto_format=False)])
                    self.client.replyMessage(Message(text=text, mention=Mention(author_id, len(author_display_name), text.find(author_display_name)), style=styles), message_object, thread_id, thread_type, ttl=120000)
                    self.client.sendLocalImage(anh_path, width=width, height=height, thread_id=thread_id, thread_type=thread_type, ttl=120000)
                    os.remove(anh_path)
                    return
            except Exception as e: logger.error(f"[AntiUndo] Lỗi khi gửi lại ảnh thu hồi: {e}")

        if original_msg_type.startswith('chat.sticker') and original_content.get('id') and original_content.get('catId'):
            self._send_sticker_reconstruction(original_content['id'], original_content['catId'], thread_id, thread_type, author_id, message_object)
            return

        if original_text:
            clean_text = original_text
            if original_text.startswith('Message(') and original_text.endswith(')'):
                match_text = re.search(r"text='([^']*)'", original_text)
                if match_text: clean_text = match_text.group(1)
                else:
                    match_title = re.search(r"title='([^']*)'", original_text)
                    if match_title and match_title.group(1): clean_text = match_title.group(1)
                    else:
                        match_desc = re.search(r"description='([^']*)'", original_text)
                        if match_desc and match_desc.group(1): clean_text = match_desc.group(1)

            text = f"➜ [UNDO TIN NHẮN]\n{author_display_name} vừa thu hồi một tin nhắn.\n➜ Nội dung gốc: '{clean_text}'"
            styles = MultiMsgStyle([MessageStyle(offset=len("➜ "), length=len("[UNDO TIN NHẮN]"), style="color", color="#db342e", auto_format=False), MessageStyle(offset=len("➜ "), length=len("[UNDO TIN NHẮN]"), style="bold", auto_format=False)])
            self.client.replyMessage(Message(text=text, mention=Mention(author_id, len(author_display_name), text.find(author_display_name)), style=styles), message_object, thread_id, thread_type, ttl=120000)
            return

        logger.warning(f"[AntiUndo] Không thể khôi phục tin nhắn thu hồi. cliMsgId: {cliMsgId_recalled}, Original message: {original_message}")
