import json
import os
import threading
import time
from zlapi import *
from zlapi.models import *
import obcore_welcome 

author  = (
    "👨‍💻 Tác giả: A Sìn\n"
    "🔄 Cập nhật: 01-11-24 v2 hotfix\n"
    "🚀 Tính năng: Chào mừng thành viên ra vào nhóm V2\n"
    "🔗 Link Font và file obcore_welcome.py code chính đã mã hóa: https://drive.google.com/file/d/1338pbNkULZOuEu3WLfkSML7lua6TbAID/view?usp=drive_link\n"
    "📌 Lưu ý:\n"
    "   1️⃣ [Bước 1] Thay imei và cookie\n"
    "   2️⃣ [Bước 2] Cài thư viện pip install pillow, pip install emoji, pip install requests. Run file chính welcome2.py\n"
    "Thư mục Font, file obcore_welcome.py và welcome2.py đặt ngang hàng nhau"
    "   3️⃣ [Bước 3] Chọn nhóm cần bật welcome. Gõ lệnh !wl on để bật chế độ welcome. Tắt bằng lệnh !wl off"
)
#pip install Pillow
#pip install emoji


SETTING_FILE = 'setting.json'

def read_settings():
    """Đọc toàn bộ nội dung từ file JSON."""
    if not os.path.exists(SETTING_FILE):  # Kiểm tra xem file có tồn tại không
        # Nếu không tồn tại, tạo file với nội dung mặc định
        write_settings({})  # Ghi vào file một đối tượng JSON rỗng
    try:
        with open(SETTING_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def write_settings(settings):
    """Ghi toàn bộ nội dung vào file JSON."""
    with open(SETTING_FILE, 'w', encoding='utf-8') as file:
        json.dump(settings, file, ensure_ascii=False, indent=4)



def get_allowed_thread_ids():
    """Lấy danh sách các groupId có giá trị true trong 'welcome'."""
    settings = read_settings()
    
    # Kiểm tra xem mục 'welcome' có tồn tại không
    welcome_settings = settings.get('welcome', {})
    
    # Lọc ra các thread_id có giá trị là True
    allowed_thread_ids = [thread_id for thread_id, is_enabled in welcome_settings.items() if is_enabled]
    
    return allowed_thread_ids

def handle_welcome_on( thread_id):
    settings = read_settings()

    # Khởi tạo thông tin welcome nếu chưa tồn tại
    if "welcome" not in settings:
        settings["welcome"] = {}

    # Nếu nhóm chưa có thông tin trong welcome, thêm nhóm vào
    if thread_id not in settings["welcome"]:
        settings["welcome"][thread_id] = False

    # Bật chế độ welcome
    settings["welcome"][thread_id] = True
    write_settings(settings)

    # Lấy tên nhóm từ bot để hiển thị
    # gr_name = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id].name
    return f"🚦Chế độ welcome đã 🟢 Bật 🎉"


def handle_welcome_off( thread_id):
    settings = read_settings()

    # Kiểm tra nếu nhóm đã có thông tin welcome
    if "welcome" in settings and thread_id in settings["welcome"]:
        # Tắt chế độ welcome
        settings["welcome"][thread_id] = False
        write_settings(settings)

        # Lấy tên nhóm từ bot để hiển thị
        # gr_name = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id].name
        return f"🚦Chế độ welcome đã 🔴 Tắt 🎉"
    else:
        return "🚦Nhóm chưa có thông tin cấu hình welcome để 🔴 Tắt 🤗"
    
def get_allow_welcome(thread_id):
    # Đọc cấu hình từ file
    settings = read_settings()

    # Kiểm tra xem 'allow_link' có tồn tại trong cấu hình không
    if 'welcome' in settings:
        # Kiểm tra xem thread_id có trong allow_link không
        return settings['welcome'].get(thread_id, False)
    else:
        # Nếu 'allow_link' không tồn tại trong cấu hình, trả về False
        return False

def initialize_group_info(bot, allowed_thread_ids):
    for thread_id in allowed_thread_ids:
        group_info = bot.fetchGroupInfo(thread_id).gridInfoMap.get(thread_id, None)  # Thêm .get để tránh lỗi khi thread_id không tồn tại
        if group_info:  # Kiểm tra nếu group_info không phải None
            # print(group_info)
            bot.group_info_cache[thread_id] = {
                "name": group_info['name'],
                "member_list": group_info['memVerList'],
                "total_member": group_info['totalMember']
            }
        else:
            print(f"Bỏ qua nhóm {thread_id}")


def delete_file(file_path):
    """Xóa tệp sau khi sử dụng."""
    try:
        os.remove(file_path)
        print(f"Đã xóa tệp: {file_path}")
    except Exception as e:
        print(f"Lỗi khi xóa tệp: {e}")

def check_member_changes(bot, thread_id):
    # Lấy thông tin hiện tại của nhóm từ API
    current_group_info = bot.fetchGroupInfo(thread_id).gridInfoMap.get(thread_id, None)
    
    # Lấy thông tin nhóm đã lưu trong cache
    cached_group_info = bot.group_info_cache.get(thread_id, None)
    
    # Nếu không có thông tin, trả về danh sách rỗng
    if not cached_group_info or not current_group_info:
        return [], []  

    # Lấy danh sách thành viên cũ và mới
    old_members = set([member.split('_')[0] for member in cached_group_info["member_list"]])  # Thành viên cũ (bỏ hậu tố '_0')
    new_members = set([member.split('_')[0] for member in current_group_info['memVerList']])  # Thành viên mới (bỏ hậu tố '_0')
    # Thành viên mới vào nhóm
    joined_members = new_members - old_members

    # Thành viên rời nhóm
    left_members = old_members - new_members

    # Cập nhật cache với thông tin mới nhất
    bot.group_info_cache[thread_id] = {
        "name": current_group_info['name'],
        "member_list": current_group_info['memVerList'],  # Giữ danh sách với hậu tố gốc
        "total_member": current_group_info['totalMember']
    }

    return joined_members, left_members


def handle_group_member(bot, message_object, author_id, thread_id, thread_type):

        # Kiểm tra sự thay đổi thành viên
    joined_members, left_members = check_member_changes(bot, thread_id)
    # Chào mừng thành viên mới
    if joined_members:
        for member_id in joined_members:
            member_info = bot.fetchUserInfo(member_id).changed_profiles[member_id]# Lấy tên thành viên mới
            user_name =member_info.zaloName
            msg=f"{user_name}"
            mention = Mention(uid=member_id, length=len(user_name), offset=msg.index(user_name))
            
            banner = obcore_welcome.create_banner(bot, member_id,thread_id,1)
            bot.sendLocalImage(banner, thread_id=thread_id, thread_type=thread_type, width=1000, height=300, message=Message(text=msg,mention=mention),ttl=86400000)
            delete_file(banner)
            
    # Tạm biệt thành viên rời nhóm
    if left_members:
        for member_id in left_members:
    
            banner=obcore_welcome.create_banner(bot, member_id,thread_id,2)
            bot.sendLocalImage(banner, thread_id=thread_id, thread_type=thread_type, width=1000, height=300,ttl=86400000)
            delete_file(banner)


def start_member_check_thread(bot, allowed_thread_ids):
    # Tạo và bắt đầu luồng để kiểm tra thành viên mới
    def check_members_loop():
        while True:
            for thread_id in allowed_thread_ids:
                if get_allow_welcome(thread_id):
                    # Chỉ kiểm tra nếu get_allow_welcome trả về True
                    handle_group_member(bot, None, None, thread_id, ThreadType.GROUP)
            time.sleep(2)   

    thread = threading.Thread(target=check_members_loop)
    thread.daemon = True  # Đảm bảo luồng kết thúc khi chương trình chính dừng
    thread.start()




class Bot(ZaloAPI):
    def __init__(self, api_key, secret_key, imei=None, session_cookies=None):
        super().__init__(api_key, secret_key, imei, session_cookies)
        self.group_info_cache = {} 
        # Trích xuất toàn bộ groupId từ gridVerMap
        all_group = self.fetchAllGroups()
        
        # Trích xuất toàn bộ groupId từ gridVerMap
        allowed_thread_ids = list(all_group.gridVerMap.keys())
        
        initialize_group_info(self, allowed_thread_ids)
        start_member_check_thread(self,allowed_thread_ids)

    



    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        # self.markAsDelivered(mid, message_object.cliMsgId, author_id, thread_id, thread_type, message_object.msgType)
        print(f"🎏 {thread_type.name} {'🙂' if thread_type.name == 'USER' else '🐞'}  {author_id}   {thread_id}")
        print(f"{message}")

        
        if not isinstance(message, str):
            return
        str_message= str(message)
        if str_message.startswith('!wl'):
            parts = str_message.split()
            if len(parts) < 2:
                response = "➜ Vui lòng nhập [on/off] sau lệnh: !wl 🤗\n➜ Ví dụ: !wl on on hoặc !wl off ✅"
            else:
                sub_action = parts[1].lower()
                if author_id!= self.uid:
                    response = "➜ Lệnh này chỉ khả thi với chủ nhân 🤗"
                elif thread_type != ThreadType.GROUP:
                    response = "➜ Lệnh này chỉ khả thi trong nhóm 🤗"
                else:
                    if sub_action == 'on':
                        response = handle_welcome_on( thread_id)
                    elif sub_action == 'off':
                        response = handle_welcome_off(thread_id)
                    else:
                        response = f"➜ Lệnh !wl {sub_action} không được hỗ trợ 🤗"
        if response:
            self.send(Message(text=f"{response}"), thread_id,thread_type)
   
        
   
#Thay imei và cookie ở đây
imei=''
session_cookies ={}

client = Bot('api_key', 'secret_key', imei=imei, session_cookies=session_cookies)
client.listen(run_forever=True, delay=0, thread=True,type='requests')

