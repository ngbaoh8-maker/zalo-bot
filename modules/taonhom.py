import re
from zlapi.models import Message
from config import ADMIN, PREFIX

# --- CẤU HÌNH CỐ ĐỊNH ---
des = {
    'version': "1.0.7",
    'credits': "ngbao",
    'description': "Tạo nhóm, Lấy link nhóm hiện tại, Lấy link TẤT CẢ nhóm và Info.",
    'power': "Quản trị viên Bot"
}

if isinstance(ADMIN, (list, tuple, set)):
    ADMIN_IDS = {str(a) for a in ADMIN}
else:
    ADMIN_IDS = {str(ADMIN)}

TTL = 20000

def is_admin(author_id):
    """Kiểm tra xem author_id có phải là Admin hay không."""
    return str(author_id) in ADMIN_IDS

# --- HÀM XỬ LÝ LỆNH TẠO NHÓM (.taonhom) ---
def handle_create_group_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh tạo nhóm. Cú pháp: .taonhom Tên 1 | Mô tả 1, Tên 2 | Mô tả 2, ...
    """
    
    if not is_admin(author_id):
        client.replyMessage(
            Message(text="❌ Bạn không có quyền sử dụng lệnh này."),
            message_object, thread_id, thread_type, ttl=TTL
        )
        return

    if message.startswith(f"{PREFIX}taonhom"):
        content = message[len(f"{PREFIX}taonhom"):].strip()
    elif message.startswith(".taonhom"):
        content = message[len(".taonhom"):].strip()
    else:
        content = message

    if not content:
        client.replyMessage(
            Message(text="❌ Sai cú pháp!\n.taonhom Tên nhóm | Mô tả nhóm (, Tên nhóm 2 | Mô tả 2,...)"),
            message_object, thread_id, thread_type, ttl=TTL
        )
        return
        
    group_requests = [req.strip() for req in content.split(',')]
    results = []
    
    for req in group_requests:
        parts = [p.strip() for p in req.split("|")]
        if len(parts) < 2:
            results.append(f"⚠️ Bỏ qua: '{req}' (Sai định dạng Tên|Mô tả)")
            continue

        group_name = parts[0]
        group_desc = parts[1]
        
        if re.search(r"(http://|https://|www\.)", group_desc, re.IGNORECASE):
            results.append(f"❌ {group_name}: Mô tả không được chứa liên kết.")
            continue

        members = [str(author_id)]
        
        try:
            response = client.createGroup(
                name=group_name,
                description=group_desc,
                members=members
            )

            if response.get("groupId"):
                gr_id = response.get("groupId")
                results.append(f"✅ {group_name} thành công. ID: {gr_id}")
            else:
                error_message = response.get('message', str(response)) 
                results.append(f"❌ {group_name} thất bại. API trả về: {error_message}")

        except Exception as e:
            results.append(f"❌ {group_name}: Lỗi khi tạo nhóm: {str(e)}")

    final_message = "✨ **Kết quả tạo nhóm:**\n" + "\n".join(results)
    
    client.replyMessage(
        Message(text=final_message),
        message_object, thread_id, thread_type, ttl=TTL
    )

# --- HÀM XỬ LÝ LỆNH LẤY LINK NHÓM HIỆN TẠI (.getlink) ---
def handle_get_group_link(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh lấy link chia sẻ của nhóm hiện tại (thread_id). Lệnh: .getlink
    """
    
    if thread_type != 2: # Giả định thread_type = 2 là group cPTA
        client.replyMessage(
            Message(text="❌ Lệnh này chỉ sử dụng được trong nhóm cPTA."),
            message_object, thread_id, thread_type, ttl=TTL
        )
        return
    
    try:
        # Giả định hàm client.getGroupShareLink() tồn tại
        response = client.getGroupShareLink(groupId=thread_id)

        if response and response.get("link"):
            group_link = response.get("link")
            client.replyMessage(
                Message(text=f"🔗 **Link nhóm cPTA:**\n{group_link}"),
                message_object, thread_id, thread_type, ttl=TTL
            )
        else:
            error_msg = response.get('message', 'Không thể tạo hoặc lấy link nhóm.') if response else 'Lỗi kết nối API.'
            client.replyMessage(
                Message(text=f"❌ Thất bại khi lấy link nhóm:\n{error_msg}"),
                message_object, thread_id, thread_type, ttl=TTL
            )

    except Exception as e:
        client.replyMessage(
            Message(text=f"❌ Lỗi ngoại lệ khi lấy link nhóm: {str(e)}"),
            message_object, thread_id, thread_type, ttl=TTL
        )


# --- HÀM XỬ LÝ LỆNH LẤY LINK TẤT CẢ CÁC NHÓM (.getalllinks) ---
def handle_get_all_group_links(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh lấy link của TẤT CẢ các nhóm bot đang tham gia. Lệnh: .getalllinks
    """
    
    if not is_admin(author_id):
        client.replyMessage(
            Message(text="❌ Bạn không có quyền sử dụng lệnh này."),
            message_object, thread_id, thread_type, ttl=TTL
        )
        return

    try:
        # Giả định hàm client.getGroups() tồn tại
        groups_response = client.getGroups() 
        
        if not groups_response or not isinstance(groups_response, list):
            client.replyMessage(
                Message(text="❌ Lỗi khi lấy danh sách nhóm hoặc bot không tham gia nhóm nào."),
                message_object, thread_id, thread_type, ttl=TTL
            )
            return

        results = []
        
        for group in groups_response:
            group_id = group.get("groupId")
            group_name = group.get("name", "Tên không rõ")
            
            if not group_id:
                continue

            try:
                # Lấy link chia sẻ
                link_response = client.getGroupShareLink(groupId=group_id)
                
                if link_response and link_response.get("link"):
                    link = link_response.get("link")
                    results.append(f"✅ **{group_name}** (ID: {group_id}):\n{link}")
                else:
                    error_msg = link_response.get('message', 'Không lấy được link.') if link_response else 'Lỗi API.'
                    results.append(f"❌ **{group_name}** (ID: {group_id}): Thất bại: {error_msg}")

            except Exception as e:
                results.append(f"❌ **{group_name}** (ID: {group_id}): Lỗi ngoại lệ: {str(e)}")

        if results:
            final_message = "📋 **Danh sách Link các nhóm bot đang tham gia:**\n\n" + "\n---\n".join(results)
        else:
            final_message = "✅ Bot hiện không tham gia nhóm nào hoặc không thể lấy dữ liệu."

        client.replyMessage(
            Message(text=final_message),
            message_object, thread_id, thread_type, ttl=TTL
        )

    except Exception as e:
        client.replyMessage(
            Message(text=f"❌ Lỗi tổng quát khi xử lý danh sách nhóm: {str(e)}"),
            message_object, thread_id, thread_type, ttl=TTL
        )

# --- HÀM XỬ LÝ LỆNH RIÊNG (.info) ---
def handle_info_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh lấy thông tin cơ bản của tin nhắn hiện tại. Lệnh: .info
    """
    
    thread_type_name = "Nhóm cPTA" if thread_type == 2 else "CPTA riêng"
    
    response_text = (
        "🔍 **Thông tin Lệnh Info:**\n"
        f"➡️ **Người dùng (Author ID):** `{author_id}`\n"
        f"➡️ **Luồng cPTA (Thread ID):** `{thread_id}`\n"
        f"➡️ **Loại cPTA (Thread Type):** {thread_type_name} ({thread_type})"
    )

    client.replyMessage(
        Message(text=response_text),
        message_object, thread_id, thread_type, ttl=TTL
    )


# --- KHAI BÁO LỆNH ---
def PTA():
    """Trả về từ điển ánh xạ lệnh đến hàm xử lý tương ứng."""
    return {
        "taonhom": handle_create_group_command,
        "getlink": handle_get_group_link,
        "getalllinks": handle_get_all_group_links,
        "info": handle_info_command
    }

# --- END OF FILE ---
