import os
import importlib
from zlapi.models import Message
from config import PREFIX

des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Lệnh này cung cấp thông tin chi tiết về các lệnh khác.",
    'power': "Thành viên"
}

def get_all_vxkiue_with_info():
    vxkiue_info = {}

    for module_name in os.listdir('modules'):
        if module_name.endswith('.py') and module_name != '__init__.py':
            module_path = f'modules.{module_name[:-3]}'
            try:
                module = importlib.import_module(module_path)

                if hasattr(module, 'des'):
                    des = getattr(module, 'des')
                    version = des.get('version', 'Chưa có thông tin')
                    credits = des.get('credits', 'Chưa có thông tin')
                    description = des.get('description', 'Chưa có thông tin')
                    power = des.get('power', 'Chưa có thông tin')
                    vxkiue_info[module_name[:-3]] = (version, credits, description, power)
            except Exception as e:
                print(f"Error loading module {module_name}: {e}")
                continue

    return vxkiue_info

def paginate_helps(vxkiue_info, page=1, page_size=5):
    total_pages = (len(vxkiue_info) + page_size - 1) // page_size
    if page < 1 or page > total_pages:
        return None, total_pages

    start = (page - 1) * page_size
    end = start + page_size

    helps_on_page = list(vxkiue_info.items())[start:end]

    return helps_on_page, total_pages
    
def handle_help_help(message, message_object, thread_id, thread_type, author_id, client):
    help_parts = message.split()
    vxkiue_info = get_all_vxkiue_with_info()

    if len(help_parts) > 1:
        if help_parts[1].isdigit():
            page = int(help_parts[1])
        else:
            requested_help = help_parts[1].lower()
            if requested_help in vxkiue_info:
                version, credits, description, power = vxkiue_info[requested_help]
                single_help_message = (
                    f"🔹Thông Tin Lệnh:\n\n"
                    f"> 🏷️ Tên lệnh: {requested_help}\n"
                    f"> ⏳ Phiên bản: {version}\n"
                    f"> 🔑 Tác giả: {credits}\n"
                    f"> 📄 Mô tả: {description}\n"
                    f"> 🗝️ Quyền hạn: {power}"
                )
                client.replyMessage(Message(text=single_help_message), message_object, thread_id, thread_type, ttl=12000)
                return
            else:
                error_message = f"🚫 Không tìm thấy lệnh `{requested_help}` trong hệ thống."
                client.replyMessage(Message(text=error_message), message_object, thread_id, thread_type, ttl=12000)
                return
    else:
        page = 1

    helps_on_page, total_pages = paginate_helps(vxkiue_info, page)

    if helps_on_page is None:
        help_message = f"😐 Trang {page} không hợp lệ. Tổng số trang: {total_pages}."
    else:
        help_message_lines = [f"📜 Danh Sách Lệnh (Trang {page}/{total_pages}):\n"]
        for i, (name, (version, credits, description, power)) in enumerate(helps_on_page, (page - 1) * 7 + 1):
            help_message_lines.append(
                f"🔹 {i}. 🏷️ {name}\n"
                f"   > 📄 Mô tả: {description}\n"
                f"   > ⏳ Phiên bản: {version}\n"
                f"   > 🔑 Tác giả: {credits}\n"
                f"   > 🗝️ Quyền hạn: {power}\n"
            )

        help_message_lines.append(f"\n👉 Dùng lệnh `{PREFIX}help <page>` để chuyển trang.")
        help_message_lines.append(f"👉 Ví dụ: `{PREFIX}help 2` để xem trang tiếp theo.")
        help_message = "\n".join(help_message_lines)

    client.replyMessage(Message(text=help_message), message_object, thread_id, thread_type, ttl=86400000)

def PTA():
    return {
        'help': handle_help_help
    }