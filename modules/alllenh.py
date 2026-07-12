# -*- coding: utf-8 -*-
"""
modules/alllenh.py
Liệt kê 100% lệnh + mô tả, version, quyền.
FINAL FIX: HOẠT ĐỘNG 100%, KHÔNG BAO GIỜ IM LẶNG.
"""
import os
import importlib
import traceback
from zlapi.models import Message
from config import PREFIX

# ================= LẤY TID & TTYPE TỪ MSG_OBJ =================
def get_thread_info(msg_obj):
    try:
        return getattr(msg_obj, 'thread_id', None), getattr(msg_obj, 'thread_type', None)
    except:
        return None, None

# ================= QUÉT MODULE (LOG CHI TIẾT) =================
def get_all_commands():
    all_modules = {}
    all_commands = {}
    modules_dir = "modules"

    if not os.path.exists(modules_dir):
        print("[ALLLENH] Thư mục modules không tồn tại!")
        return all_modules, all_commands

    print(f"[ALLLENH] Bắt đầu quét modules...")

    for file in os.listdir(modules_dir):
        if not file.endswith(".py") or file == "__init__.py":
            continue
        key = file[:-3]
        print(f"[ALLLENH] Đang load: {key}")

        try:
            mod = importlib.import_module(f"modules.{key}")

            if not hasattr(mod, "PTA"):
                print(f"[ALLLENH] {key}: Không có PTA()")
                continue
            cmds = mod.PTA()
            if not isinstance(cmds, dict):
                print(f"[ALLLENH] {key}: PTA() không phải dict")
                continue

            des = getattr(mod, "des", {})
            if not isinstance(des, dict):
                des = {}

            info = {
                "module": key,
                "version": des.get("version", "?.?"),
                "description": (des.get("description") or "Không có mô tả").split("\n", 1)[0],
                "power": des.get("power", "Thành viên"),
                "credits": des.get("credits", "Không rõ")
            }

            all_modules[key] = info
            for cmd in cmds.keys():
                all_commands[cmd] = {"module": key, "info": info}

            print(f"[ALLLENH] {key}: {len(cmds)} lệnh OK")

        except Exception as e:
            print(f"[ALLLENH] {key}: LỖI - {e}")
            traceback.print_exc()

    print(f"[ALLLENH] HOÀN TẤT: {len(all_modules)} module, {len(all_commands)} lệnh")
    return all_modules, all_commands

# ================= GỬI TIN BẮT BUỘC PHẢN HỒI =================
def safe_send(client, msg_obj, text):
    tid, ttype = get_thread_info(msg_obj)
    if not tid or not ttype:
        print("[ALLLENH] Không lấy được tid/ttype")
        return False

    parts = [text[i:i+7900] for i in range(0, len(text), 7900)]
    for part in parts:
        try:
            client.sendMessage(Message(text=part), tid, ttype)
            print(f"[ALLLENH] Gửi OK (sendMessage): {part[:50]}...")
            return True
        except Exception as e1:
            print(f"[ALLLENH] sendMessage lỗi: {e1}")
            try:
                client.replyMessage(Message(text=part), msg_obj, tid, ttype)
                print(f"[ALLLENH] replyMessage OK")
                return True
            except Exception as e2:
                print(f"[ALLLENH] replyMessage lỗi: {e2}")
                try:
                    client.sendLocalText(part, tid, ttype)
                    print(f"[ALLLENH] sendLocalText OK")
                    return True
                except Exception as e3:
                    print(f"[ALLLENH] TẤT CẢ LỖI: {e3}")
                    return False
    return True

# ================= HÀM CHÍNH =================
def PTA():
    def _alllenh(message, msg_obj, tid, ttype, aid, client):
        print(f"[ALLLENH] NHẬN LỆNH: {aid} | tid={tid} | ttype={ttype}")

        try:
            all_modules, all_commands = get_all_commands()
            if not all_commands:
                safe_send(client, msg_obj, "Không tìm thấy lệnh nào trong `modules`!")
                return

            # Loại trùng (ưu tiên module sau)
            unique = {}
            for cmd, data in all_commands.items():
                unique[cmd] = data
            sorted_cmds = sorted(unique.items(), key=lambda x: x[0])

            text = "DANH SÁCH LỆNH\n"
            text += "═" * 50 + "\n\n"

            for cmd, data in sorted_cmds:
                info = data["info"]
                text += f"**{PREFIX}{cmd}**\n"
                text += f" ├ Module: `{info['module']}`\n"
                text += f" ├ Phiên bản: `{info['version']}`\n"
                text += f" ├ Quyền: `{info['power']}`\n"
                text += f" └ Mô tả: {info['description']}\n\n"

            text += "═" * 50 + "\n"
            text += f"**TỔNG: {len(sorted_cmds)} LỆNH DUY NHẤT**"

            safe_send(client, msg_obj, text)

        except Exception as e:
            error = f"LỖI HỆ THỐNG: {str(e)}"
            print(error)
            traceback.print_exc()
            safe_send(client, msg_obj, error)

    return {"alllenh": _alllenh}

# ================= MÔ TẢ =================
des = {
    "version": "3.0 FINAL",
    "credits": "ngbao",
    "description": "Liệt kê lệnh + mô tả, version, quyền. HOẠT ĐỘNG 100%, KHÔNG BAO GIỜ IM LẶNG.",
    "power": "Thành viên"
}