import os
import time
import threading
import json
from zlapi.models import Message, Mention, MultiMention, MultiMsgStyle, MessageStyle, ThreadType
from config import PREFIX

des = {
    'version': "2.0.0",
    'credits': "Antigravity",
    'description': "Treo ngôn ẩn tagall với nhiều màu sắc và cấu hình delay",
    'power': "Quản trị viên Bot"
}

CONFIG_PATH = "treongon_config.json"
treo_threads = {}  # Store: {thread_id: (stop_event, start_time)}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "delay": 5.0,
        "color": "#F7B503",
        "content": "Chào mọi người!"
    }

def save_config(config):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi lưu cấu hình: {e}")

def is_admin(author_id):
    try:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
        if not os.path.exists(path):
            path = 'seting.json'
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        admin_main = str(data.get('admin', ''))
        vip = [str(x) for x in data.get('vip_adm', [])]
        adm_list = [str(x) for x in data.get('adm', [])]
        
        author_str = str(author_id)
        
        try:
            from config import ADMIN
            config_admin = str(ADMIN)
        except Exception:
            config_admin = ""
            
        admins = set([admin_main, config_admin] + vip + adm_list)
        if "" in admins:
            admins.remove("")
            
        return author_str in admins
    except Exception as e:
        print(f"Lỗi kiểm tra admin: {e}")
        try:
            from config import ADMIN
            return str(author_id) == str(ADMIN)
        except:
            return False

def parse_color(color_name):
    color_name = color_name.strip().lower()
    mapping = {
        "đỏ": "#DB342E", "do": "#DB342E", "red": "#DB342E",
        "xanh lá": "#15A85F", "xanh la": "#15A85F", "xanh": "#15A85F", "green": "#15A85F",
        "cam": "#F27806", "orange": "#F27806",
        "vàng": "#F7B503", "vang": "#F7B503", "yellow": "#F7B503"
    }
    if color_name in mapping:
        return mapping[color_name]
    if color_name.startswith("#"):
        return color_name
    if len(color_name) == 6 and all(c in "0123456789abcdef" for c in color_name):
        return "#" + color_name
    return None

def format_duration(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours} giờ")
    if minutes > 0:
        parts.append(f"{minutes} phút")
    parts.append(f"{secs} giây")
    return " ".join(parts)

def handle_treongon_command(message, message_object, thread_id, thread_type, author_id, client):
    global treo_threads
    
    # Kiểm tra quyền admin
    if not is_admin(author_id):
        client.replyMessage(
            Message(text="⚠️ Bạn không có quyền sử dụng lệnh này."),
            message_object, thread_id, thread_type, ttl=10000
        )
        return

    parts = message.split(maxsplit=2)
    if len(parts) < 2:
        help_text = (
            f"ℹ️ HƯỚNG DẪN SỬ DỤNG TREONGON:\n"
            f"• {PREFIX}treo on/start: Bật treo ngôn trong nhóm này\n"
            f"• {PREFIX}treo stop/off: Tắt treo ngôn\n"
            f"• {PREFIX}treo set [nội dung]: Đặt ngôn cần treo\n"
            f"• {PREFIX}treo mau [đỏ/xanh/cam/vàng/mã màu]: Đặt màu chữ\n"
            f"• {PREFIX}treo delay [giây]: Đặt độ trễ gửi tin\n"
            f"• {PREFIX}treo setting: Xem cấu hình và các nhóm đang treo"
        )
        client.replyMessage(Message(text=help_text), message_object, thread_id, thread_type)
        return

    subcmd = parts[1].lower()

    if subcmd in ["on", "start"]:
        config = load_config()
        content = config.get("content", "")
        delay = config.get("delay", 5.0)
        color = config.get("color", "#F7B503")

        if not content:
            client.replyMessage(Message(text="❌ Chưa thiết lập ngôn treo! Hãy dùng lệnh: treo set <ngôn>"), message_object, thread_id, thread_type)
            return

        if thread_id in treo_threads:
            # Stop existing first
            stop_event, _ = treo_threads[thread_id]
            stop_event.set()
            del treo_threads[thread_id]

        stop_event = threading.Event()
        start_time = time.time()
        treo_threads[thread_id] = (stop_event, start_time)

        def treo_loop(tid, ttype, se, text, dl, clr):
            while not se.is_set():
                try:
                    # Tạo style màu sắc và in đậm
                    styles = MultiMsgStyle([
                        MessageStyle(offset=0, length=len(text), style="color", color=clr, auto_format=False),
                        MessageStyle(offset=0, length=len(text), style="bold", auto_format=False)
                    ])
                    # Tạo mention ẩn tagall (offset = -1)
                    mention = Mention("-1", 1, -1, False)
                    multi_mention = MultiMention([mention])
                    
                    client.send(
                        Message(text=text, mention=multi_mention, style=styles),
                        thread_id=tid,
                        thread_type=ttype
                    )
                except Exception as e:
                    print(f"Lỗi treo ngôn: {e}")

                # Sleep ngắt quãng để tắt nhanh khi gọi stop
                for _ in range(int(dl * 10)):
                    if se.is_set():
                        break
                    time.sleep(0.1)
                
                remainder = (dl * 10) - int(dl * 10)
                if remainder > 0 and not se.is_set():
                    time.sleep(remainder / 10.0)

        t = threading.Thread(target=treo_loop, args=(thread_id, thread_type, stop_event, content, delay, color))
        t.daemon = True
        t.start()

        client.replyMessage(
            Message(text=f"🚀 Đã bật treo ngôn ẩn tagall!\n⏱️ Delay: {delay} giây\n🎨 Màu: {color}\n📝 Nội dung: {content}"),
            message_object, thread_id, thread_type
        )

    elif subcmd in ["stop", "off"]:
        if thread_id in treo_threads:
            stop_event, _ = treo_threads[thread_id]
            stop_event.set()
            del treo_threads[thread_id]
            client.replyMessage(Message(text="✅ Đã tắt treo ngôn trong nhóm này."), message_object, thread_id, thread_type)
        else:
            client.replyMessage(Message(text="⚠️ Nhóm này hiện không treo ngôn."), message_object, thread_id, thread_type)

    elif subcmd in ["set", "ngon"]:
        if len(parts) < 3:
            client.replyMessage(Message(text="❌ Vui lòng nhập nội dung ngôn cần treo!"), message_object, thread_id, thread_type)
            return
        
        content = parts[2].strip()
        config = load_config()
        config["content"] = content
        save_config(config)
        client.replyMessage(Message(text=f"✅ Đã set ngôn treo thành công:\n👉 {content}"), message_object, thread_id, thread_type)

    elif subcmd in ["mau", "màu"]:
        if len(parts) < 3:
            client.replyMessage(Message(text="❌ Vui lòng nhập màu (đỏ, xanh, cam, vàng hoặc mã hex #FFFFFF)!"), message_object, thread_id, thread_type)
            return
        
        color_input = parts[2].strip()
        parsed_clr = parse_color(color_input)
        if not parsed_clr:
            client.replyMessage(Message(text="❌ Màu không hợp lệ! Vui lòng chọn: đỏ, xanh, cam, vàng hoặc mã hex (ví dụ: #FF00FF)."), message_object, thread_id, thread_type)
            return
        
        config = load_config()
        config["color"] = parsed_clr
        save_config(config)
        client.replyMessage(Message(text=f"✅ Đã đổi màu treo sang: {color_input} ({parsed_clr})"), message_object, thread_id, thread_type)

    elif subcmd == "delay":
        if len(parts) < 3:
            client.replyMessage(Message(text="❌ Vui lòng nhập số giây delay!"), message_object, thread_id, thread_type)
            return
        
        try:
            delay_val = float(parts[2].strip())
            if delay_val <= 0:
                raise ValueError()
        except ValueError:
            client.replyMessage(Message(text="❌ Số giây delay phải là một số lớn hơn 0!"), message_object, thread_id, thread_type)
            return
        
        config = load_config()
        config["delay"] = delay_val
        save_config(config)
        client.replyMessage(Message(text=f"✅ Đã đặt delay treo sang: {delay_val} giây"), message_object, thread_id, thread_type)

    elif subcmd == "setting":
        config = load_config()
        color_val = config.get("color", "#F7B503")
        delay_val = config.get("delay", 5.0)
        content_val = config.get("content", "")
        
        active_list = []
        now_time = time.time()
        for idx, (tid, (stop_event, start_time)) in enumerate(treo_threads.items(), 1):
            duration = now_time - start_time
            dur_str = format_duration(duration)
            try:
                ginfo = client.fetchGroupInfo(tid).gridInfoMap.get(tid)
                gname = ginfo.name if ginfo else "Nhóm không xác định"
            except Exception:
                gname = "Không thể lấy tên nhóm"
            active_list.append(f"{idx}. {gname} ({tid}) - Đã treo: {dur_str}")
            
        active_str = "\n".join(active_list) if active_list else "Không có nhóm nào đang treo."
        
        sett_msg = (
            f"⚙️ CẤU HÌNH TREO NGÔN:\n"
            f"🎨 Màu sắc: {color_val}\n"
            f"⏱️ Delay: {delay_val} giây\n"
            f"📝 Nội dung: {content_val}\n\n"
            f"👥 DANH SÁCH NHÓM ĐANG TREO:\n"
            f"{active_str}"
        )
        client.replyMessage(Message(text=sett_msg), message_object, thread_id, thread_type)

    else:
        client.replyMessage(Message(text="❌ Lệnh phụ không hợp lệ! Hãy gõ lệnh treo để xem hướng dẫn."), message_object, thread_id, thread_type)

def PTA():
    return {
        'treo': handle_treongon_command,
        'treongon': handle_treongon_command
    }
