from zlapi.models import *
# Giả sử file config có định nghĩa ADMIN ID và PREFIX (ví dụ: '!')
from config import ADMIN, PREFIX 

# --- HÀM HỖ TRỢ (NÊN ĐẶT Ở FILE RIÊNG, TẠM THỜI ĐỂ Ở ĐÂY) ---
def get_user_name_by_id(client, author_id):
    """Lấy tên Zalo của người dùng bằng ID."""
    try:
        user_info = client.fetchUserInfo(author_id)
        author_info = user_info.changed_profiles.get(author_id, {}) if user_info and user_info.changed_profiles else {}
        return author_info.get('zaloName', 'Không xác định')
    except Exception as e:
        print(f"Lỗi lấy tên người dùng {author_id}: {e}")
        return 'Không xác định'

def is_admin(author_id):
    """Kiểm tra xem ID người dùng có phải là ADMIN hay không."""
    # Chuyển cả hai sang string để so sánh an toàn
    return str(author_id) == str(ADMIN)

def send_bot_reply(client, message_object, thread_id, thread_type, author_id, text_content):
    """Hàm gửi tin nhắn phản hồi có gắn thẻ (mention) người dùng."""
    try:
        name = get_user_name_by_id(client, author_id)
        prefix_len = len("🚦")
        mention = Mention(author_id, offset=prefix_len, length=len(name))

        client.replyMessage(
            Message(
                text=f"🚦{name}\n{text_content}",
                mention=mention
            ),
            message_object,
            thread_id,
            thread_type,
            ttl=86400000
        )
    except Exception as e:
        print(f"Lỗi khi gửi phản hồi: {e}")

# =================================================================
#                         CLASS CHÍNH 
# =================================================================

class NotificationPlugin:
    """Class chứa các lệnh quản lý thông báo nhóm chat."""
    
    def __init__(self, client=None):
        # Có thể dùng để lưu trữ trạng thái nếu cần
        self.client = client 
        pass

    def setnotify(self, message, message_object, thread_id, thread_type, author_id, client):
        """
        Lệnh: <PREFIX>tb <on/off> [all]
        - Đặt thông báo nhóm hiện tại hoặc tất cả các nhóm
        """
        try:
            parts = message.strip().split()
            
            # 1. Kiểm tra quyền ADMIN
            if not is_admin(author_id):
                send_bot_reply(client, message_object, thread_id, thread_type, author_id, 
                               "❌ Bạn không có quyền sử dụng lệnh này. Chỉ ADMIN mới có thể.")
                return
                
            # 2. Kiểm tra cú pháp
            if len(parts) < 2 or parts[1].lower() not in ['on', 'off']:
                send_bot_reply(client, message_object, thread_id, thread_type, author_id, 
                               f"⚠️ Vui lòng dùng đúng cú pháp: `{PREFIX}tb <on/off> [all]`")
                return
                
            action = parts[1].lower()
            is_all = len(parts) > 2 and parts[2].lower() == 'all'
            
            # 3. Định nghĩa hành động (1=Tắt, 3=Bật)
            if action == 'on':
                notify_level = 3
                success_msg_prefix = "✅ Đã bật thông báo cho"
            else: # action == 'off'
                notify_level = 1
                success_msg_prefix = "🔕 Đã tắt thông báo cho"
            
            # 4. Thực hiện hành động
            if is_all:
                # Lệnh: <PREFIX>tb <on/off> all
                all_grid = client.fetchAllGroups().gridVerMap.keys()
                group_count = 0
                
                for grid in all_grid:
                    try:
                        client.setNotifyGroup(grid, notify_level)
                        group_count += 1
                    except Exception as ex:
                        # Bỏ qua các nhóm không thể set notify
                        continue 

                send_bot_reply(client, message_object, thread_id, thread_type, author_id, 
                               f"{success_msg_prefix} **{group_count}** nhóm/cộng đồng.")
            
            else:
                # Lệnh: <PREFIX>tb <on/off> (Chỉ nhóm hiện tại)
                group_info = client.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
                group_type_name = "Cộng đồng" if group_info.type == 2 else "Nhóm chat"
                
                client.setNotifyGroup(thread_id, notify_level) 
                
                send_bot_reply(client, message_object, thread_id, thread_type, author_id, 
                               f"{success_msg_prefix} **{group_type_name}** `{group_info.name}`.")
                
        except Exception as e:
            error_msg = f"Lỗi khi xử lý lệnh thông báo: {e}"
            print(error_msg)
            send_bot_reply(client, message_object, thread_id, thread_type, author_id, 
                           f"🔥 Đã xảy ra lỗi hệ thống: `{str(e)}`")


def hat():
    """Hàm trả về dictionary các lệnh (plugins) cho bot framework."""
    # Khởi tạo instance của Class và trả về method setnotify
    plugin_instance = NotificationPlugin()
    return {
        'tb': plugin_instance.setnotify
    }

# Nếu không dùng hàm PTA(), bạn có thể gọi trực tiếp:
# plugin = NotificationPlugin()
# lệnh 'tb' sẽ là plugin.setnotify
