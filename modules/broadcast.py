import os
import json
import time
import threading
from datetime import datetime
from zlapi.models import Message, MessageStyle, MultiMsgStyle, ThreadType

des = {
    "version": "1.0.0",
    "credits": "ngbao",
    "description": "Gửi tin nhắn tới tất cả bạn bè.",
    "power": "Quản trị viên Bot"
}

BROADCAST_STATUS = "modules/cache/broadcast_status.json"
json_lock = threading.Lock()


def load_json(path, default):
    with json_lock:
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default


def save_json(path, data):
    with json_lock:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except:
            pass


def is_admin(author_id, ADMIN):
    return author_id in ADMIN if isinstance(ADMIN, list) else author_id == ADMIN


# ========== AUTO BROADCAST THREAD ==========
def auto_broadcast_thread(client):
    print("[BROADCAST] Auto thread started.")
    
    while True:
        try:
            state = load_json(BROADCAST_STATUS, {"on": False, "interval": 60, "content": "", "last_send": 0})
            
            if not state.get("on", False):
                time.sleep(10)
                continue
            
            interval = int(state.get("interval", 60)) * 60
            now = int(time.time())
            
            if now - state.get("last_send", 0) >= interval:
                print(f"[BROADCAST] Đang gửi tin nhắn tự động...")
                send_broadcast(client, state.get("content", ""))
                state["last_send"] = now
                save_json(BROADCAST_STATUS, state)
                print(f"[BROADCAST] Đã gửi tin nhắn tự động lúc {datetime.now().strftime('%H:%M:%S')}")
            
            time.sleep(5)
        
        except Exception as e:
            print(f"[BROADCAST] Lỗi auto thread: {e}")
            time.sleep(10)


# ========== SEND BROADCAST ==========
def send_broadcast(client, content):
    if not content or not content.strip():
        print("[BROADCAST] Nội dung tin nhắn trống!")
        return 0
    
    try:
        # Lấy danh sách bạn bè
        friends_data = client.fetchFriends()
        friends = friends_data.friends if hasattr(friends_data, 'friends') else friends_data
        
        if not friends:
            print("[BROADCAST] Không có bạn bè nào để gửi!")
            return 0
        
        total_friends = len(friends)
        print(f"[BROADCAST] Tìm thấy {total_friends} bạn bè. Đang gửi...")
        
        success = 0
        fail = 0
        
        for i, friend in enumerate(friends, 1):
            try:
                # Lấy UID của bạn bè
                if hasattr(friend, 'uid'):
                    uid = friend.uid
                elif hasattr(friend, 'id'):
                    uid = friend.id
                elif isinstance(friend, str):
                    uid = friend
                else:
                    uid = str(friend)
                
                # Gửi tin nhắn
                client.sendMessage(Message(text=content), uid, ThreadType.USER)
                success += 1
                
                # Hiển thị tiến trình
                if i % 10 == 0 or i == total_friends:
                    print(f"[BROADCAST] Đã gửi {i}/{total_friends}...")
                
                # Delay để tránh spam
                time.sleep(0.3)
                
            except Exception as e:
                fail += 1
                print(f"[BROADCAST] Lỗi gửi tới UID {uid}: {e}")
                time.sleep(0.5)
                continue
        
        print(f"[BROADCAST] Hoàn thành! Thành công: {success}/{total_friends}, Thất bại: {fail}")
        return success
        
    except Exception as e:
        print(f"[BROADCAST] Lỗi khi lấy danh sách bạn bè: {e}")
        return 0


# ========== HANDLE COMMAND ==========
def handle_broadcast(message, message_object, thread_id, thread_type, author_id, client):
    try:
        from config import ADMIN, PREFIX
        
        # Tách phần lệnh
        parts = message.strip().split()
        if len(parts) == 0:
            return
        
        # Xác định tên người gửi (sửa lại không dùng bot)
        name = str(author_id)  # Mặc định dùng author_id
        
        def reply(txt):
            try:
                # Thử reply trước, nếu không được thì send
                try:
                    client.replyMessage(
                        Message(text=f"📢 Broadcast\n└ {txt}"),
                        message_object, thread_id, thread_type
                    )
                except:
                    # Nếu không reply được thì gửi tin nhắn bình thường
                    client.sendMessage(
                        Message(text=f"📢 Broadcast\n└ {txt}"),
                        thread_id, thread_type
                    )
            except Exception as e:
                print(f"[BROADCAST] Lỗi khi reply: {e}")
        
        # Kiểm tra quyền admin
        if not is_admin(author_id, ADMIN):
            reply("❌ Bạn không có quyền sử dụng lệnh này!")
            return
        
        # Lấy trạng thái hiện tại
        state = load_json(BROADCAST_STATUS, {"on": False, "interval": 60, "content": "", "last_send": 0})
        
        # Kiểm tra lệnh
        if len(parts) < 2:
            reply(
                f"📖 Hướng dẫn sử dụng:\n"
                f"├ {PREFIX}bc send <nội dung> - Gửi ngay\n"
                f"├ {PREFIX}bc on <phút> <nội dung> - Bật auto\n"
                f"├ {PREFIX}bc off - Tắt auto\n"
                f"├ {PREFIX}bc info - Xem thông tin\n"
                f"└ {PREFIX}bc list - Xem số bạn bè"
            )
            return
        
        cmd = parts[1].lower()
        
        # Gửi ngay lập tức
        if cmd == "send":
            if len(parts) < 3:
                reply("❌ Thiếu nội dung tin nhắn!")
                return
            
            content = " ".join(parts[2:])
            reply(f"🔄 Đang gửi tin nhắn tới tất cả bạn bè...")
            
            # Gửi tin nhắn trong thread riêng để không block
            def send_async():
                count = send_broadcast(client, content)
                reply(f"✅ Đã gửi thành công tới {count} bạn bè!")
            
            threading.Thread(target=send_async, daemon=True).start()
            return
        
        # Xem danh sách bạn bè
        elif cmd == "list":
            try:
                friends_data = client.fetchFriends()
                friends = friends_data.friends if hasattr(friends_data, 'friends') else friends_data
                reply(f"📞 Bạn có {len(friends)} bạn bè trong danh sách.")
            except Exception as e:
                reply(f"❌ Lỗi khi lấy danh sách bạn bè: {e}")
            return
        
        # Bật auto broadcast
        elif cmd == "on":
            if len(parts) < 4:
                reply(f"❌ Sử dụng: {PREFIX}bc on <số_phút> <nội_dung>")
                return
            
            try:
                interval = int(parts[2])
                if interval < 1:
                    reply("❌ Thời gian phải lớn hơn 0 phút!")
                    return
            except:
                reply("❌ Thời gian phải là số!")
                return
            
            content = " ".join(parts[3:])
            state["on"] = True
            state["interval"] = interval
            state["content"] = content
            state["last_send"] = 0
            save_json(BROADCAST_STATUS, state)
            
            reply(f"✅ Đã bật auto broadcast mỗi {interval} phút!\nNội dung: {content[:50]}..." if len(content) > 50 else content)
            return
        
        # Tắt auto broadcast
        elif cmd == "off":
            state["on"] = False
            save_json(BROADCAST_STATUS, state)
            reply("✅ Đã tắt auto broadcast!")
            return
        
        # Xem thông tin
        elif cmd == "info":
            status = "🟢 BẬT" if state.get("on") else "🔴 TẮT"
            interval = state.get("interval", 60)
            content = state.get("content", "")
            last_send = state.get("last_send", 0)
            
            if last_send:
                last_time = datetime.fromtimestamp(last_send).strftime('%H:%M:%S %d/%m/%Y')
            else:
                last_time = "Chưa gửi lần nào"
            
            reply(
                f"📊 Thông tin Broadcast:\n"
                f"├ Trạng thái: {status}\n"
                f"├ Chu kỳ: {interval} phút\n"
                f"├ Lần gửi cuối: {last_time}\n"
                f"└ Nội dung: {content[:100]}..." if len(content) > 100 else content
            )
            return
        
        else:
            reply("❌ Lệnh không hợp lệ! Gõ {prefix}bc để xem hướng dẫn.")
            
    except Exception as e:
        print(f"[BROADCAST] Lỗi xử lý lệnh: {e}")


def PTA():
    return {
        "ac": handle_broadcast
    }


# Hàm khởi động module (không cần bot parameter)
def on_load(client):
    print("[BROADCAST] Module đã được tải!")
    # Khởi động thread auto broadcast
    threading.Thread(target=auto_broadcast_thread, args=(client,), daemon=True).start()