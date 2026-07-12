# modules/outgradd/outgradd.py

import os
import json
import time
import threading
import logging
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
from zlapi import ZaloAPIException

logger = logging.getLogger(__name__)

des = {
    'version': "1.1.0",
    'credits': "ngbao",
    'description': "Chống add vào nhóm lạ.",
    'power': "Admin"
}

# Thư mục chính: bott/UID/
def get_bot_folder(client):
    uid = str(client.uid)
    folder = f"bott/{uid}"
    os.makedirs(folder, exist_ok=True)
    return folder

def get_paths(client):
    folder = get_bot_folder(client)
    return {
        "status": os.path.join(folder, "status.json"),
        "box":    os.path.join(folder, "box.json")
    }

lock = threading.Lock()

# Load/Save trạng thái on/off
def load_status(client):
    path = get_paths(client)["status"]
    if not os.path.exists(path):
        return {"enabled": False}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"enabled": False}

def save_status(client, data):
    path = get_paths(client)["status"]
    with lock:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[OutGrAdd] Lỗi lưu status: {e}")

# Load/Save danh sách nhóm đã biết
def load_known_groups(client):
    path = get_paths(client)["box"]
    if not os.path.exists(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(map(str, data))
    except:
        return set()

def save_known_groups(client, groups_set):
    path = get_paths(client)["box"]
    with lock:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(list(groups_set), f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[OutGrAdd] Lỗi lưu box.json: {e}")

def style():
    return MultiMsgStyle([MessageStyle(offset=0, length=9999, style="font", size="10", auto_format=False)])

# Task quét nhóm mới liên tục
def monitor_task(client):
    if not load_status(client).get("enabled", False):
        return

    try:
        all_groups = client.fetchAllGroups()
        if not hasattr(all_groups, "gridVerMap"):
            return

        current_ids = {str(gid) for gid in all_groups.gridVerMap.keys()}
        known = load_known_groups(client)
        new_groups = current_ids - known

        for gid in new_groups:
            try:
                group_name = "Không rõ tên nhóm"
                member_count = "?"
                try:
                    info = client.fetchGroupInfo(gid)
                    if info and hasattr(info, "gridInfoMap") and gid in info.gridInfoMap:
                        g = info.gridInfoMap[gid]
                        group_name = g.get("name", "Không rõ")
                        member_count = g.get("totalMember", "?")
                except:
                    pass

                logger.info(f"[OutGrAdd] Bị mời vào nhóm mới → {gid} | {group_name}")

                # ======== STYLE NHIỀU MÀU ========
                p1 = f"[ ANTI ADD ]\n\nNhóm: {group_name}\n"
                p2 = f"Thành viên: {member_count}\n"
                p3 = "Mời Cái Địt Con Mẹ mày\n"

                style_dict = {
                    "styles": [
                        {"start": 0, "len": len(p1), "st": "b,c_DB342E,f_18"},
                        {"start": len(p1), "len": len(p2), "st": "b,c_F27806,f_18"},
                        {"start": len(p1)+len(p2), "len": len(p3), "st": "b,c_4287F5,f_18"},
                    ],
                    "ver": 0
                }

                full_text = p1 + p2 + p3

                # ======== Gửi tin nhắn có màu + tự xoá ========
                client.sendMessage(
                    message=Message(
                        text=full_text,
                        style=style_dict
                    ),
                    thread_id=gid,
                    thread_type=ThreadType.GROUP,
                    ttl=60000
                )

                # ======== Gửi danh thiếp trước khi out ========
                CARD_UID = "8160528798217544120"  # UID người nhận danh thiếp
                CARD_CONTENT = "LH Chủ Bot Rồi Mời nhá? 💗"

                try:
                    user_info = client.fetchUserInfo(CARD_UID).get(CARD_UID, {})
                    avatar_url = user_info.get("avatar", "")
                except:
                    avatar_url = ""

                client.sendBusinessCard(
                    userId=CARD_UID,
                    qrCodeUrl=avatar_url,
                    phone=CARD_CONTENT,
                    thread_id=gid,
                    thread_type=ThreadType.GROUP,
                    ttl=60000
                )

                time.sleep(0.1)

                # Rời nhóm
                imei = getattr(client, 'imei', None)
                if imei:
                    client.leaveGroup(grid=gid, imei=imei, silent=True)
                    logger.info(f"[OutGrAdd] ĐÃ OUT + CHỬI: {gid}")
                else:
                    logger.error("[OutGrAdd] Không tìm thấy IMEI!")

                # Cập nhật danh sách
                known.add(gid)
                save_known_groups(client, known)

            except Exception as e:
                logger.error(f"[OutGrAdd] Lỗi xử lý nhóm {gid}: {e}")

    except Exception as e:
        logger.error(f"[OutGrAdd] Lỗi monitor_task: {e}")
    finally:
        if load_status(client).get("enabled", False):
            threading.Timer(12, monitor_task, args=(client,)).start()

# Bật/tắt chế độ
def toggle_auto(client, enable: bool):
    save_status(client, {"enabled": enable})
    if enable:
        try:
            all_groups = client.fetchAllGroups()
            if hasattr(all_groups, "gridVerMap"):
                current = {str(gid) for gid in all_groups.gridVerMap.keys()}
                save_known_groups(client, current)
                logger.info(f"[OutGrAdd] ĐÃ LƯU {len(current)} nhóm vào bott/{client.uid}/box.json")
        except:
            pass
        monitor_task(client)
        logger.info("[OutGrAdd] ĐÃ BẬT – Đang bảo vệ bot ✅")
    else:
        logger.info("[OutGrAdd] ĐÃ TẮT")

# Lệnh .outgradd on/off
def handle_outgradd_command(message, message_object, thread_id, thread_type, author_id, client):
    styles = style()
    prefix = getattr(client, "prefix", ".")



    parts = message.strip().split()
    if len(parts) < 2:
        client.replyMessage(Message(text=f"Dùng:\n{prefix}outgradd on\n{prefix}outgradd off", style=styles),
                            message_object, thread_id, thread_type, ttl=120000)
        return

    action = parts[1].lower()
    if action == "on":
        toggle_auto(client, True)
        client.replyMessage(Message(text="ĐÃ BẬT OUT GROUP KHI BỊ ADD\n"
                                        "→ Khởi Động Thành Công\n"
                                        "→ Bị Thêm Vào Nhóm = Rời Nhóm + Chửi\n"
                                        "→ Chúc Bạn Sài Bot Vui Vẻ 🛡️", style=styles),
                            message_object, thread_id, thread_type, ttl=120000)
    elif action == "off":
        toggle_auto(client, False)
        client.replyMessage(Message(text="ĐÃ TẮT OUTGRADD", style=styles),
                            message_object, thread_id, thread_type, ttl=120000)
    else:
        client.replyMessage(Message(text="Lệnh sai! Chỉ có on/off", style=styles),
                            message_object, thread_id, thread_type, ttl=60000)

# Khi bot khởi động
def on_start(client):
    if load_status(client).get("enabled", False):
        logger.info(f"[OutGrAdd] Bot UID {client.uid} khởi động – chế độ OUTGRADD đang BẬT")
        try:
            all_groups = client.fetchAllGroups()
            if hasattr(all_groups, "gridVerMap"):
                current = {str(gid) for gid in all_groups.gridVerMap.keys()}
                save_known_groups(client, current)
                logger.info(f"[OutGrAdd] ĐÃ CẬP NHẬT {len(current)} nhóm khi khởi động")
        except:
            pass
        monitor_task(client)
        
def PTA():
    return {
        'atadd': handle_outgradd_command
    }
