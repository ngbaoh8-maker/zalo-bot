import os
import json
import time
import requests
from zlapi.models import Message, ThreadType

des = {
    'version': "1.5",
    'credits': "ngbao",
    'description': "Gửi tin quảng cáo kèm hình ảnh",
    'power': "Admin"
}

DATA = "modules/data/adv"
os.makedirs(DATA, exist_ok=True)

FILE_TEXT = f"{DATA}/content.txt"
FILE_UID = f"{DATA}/uids.json"
FILE_IMG = f"{DATA}/images.json"


# ================================
# LOAD / SAVE HELPERS
# ================================
def read_file(path, default=""):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def write_file(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ================================
# DOWNLOAD IMAGE
# ================================
def download_images(img_list):
    folder = "temp_adv"
    os.makedirs(folder, exist_ok=True)

    local = []
    for i, url in enumerate(img_list):
        try:
            if not url.startswith("http"):
                url = "https://" + url
            r = requests.get(url, timeout=10)
            p = f"{folder}/adv_{i}_{int(time.time())}.jpg"
            with open(p, "wb") as f:
                f.write(r.content)
            local.append(p)
        except:
            pass

    return local


# ================================
# SEND PACKAGE (text + image)
# ================================
def send_adv(client, uid, text, images):
    try:
        # send images first
        if images:
            local = download_images(images)
            if local:
                client.sendMultiLocalImage(local, uid, ThreadType.USER, ttl=300000)
                for p in local:
                    try: os.remove(p)
                    except: pass
                time.sleep(0.3)

        # send text
        if text:
            client.sendMessage(Message(text=text), uid, ThreadType.USER, ttl=300000)

        return True
    except Exception as e:
        print("ERR SEND:", e)
        return False


# ================================
# COMMAND PROCESS
# ================================
def handle_adv_cmd(message, msg_obj, tid, ttype, author, client):

    text = (msg_obj.text or "").strip()
    if not text:
        return

    args = text.split()
    cmd = args[0].lower().replace(".", "").replace("/", "")

    if cmd != "adv":
        return

    if len(args) == 1:
        client.replyMessage(Message(text="⚠ Dùng: adv help"), msg_obj, tid, ttype)
        return

    # HELP
    if args[1] == "help":
        client.replyMessage(Message(text=
            "💬 MENU ADV (TEXT + ẢNH)\n"
            "──────────────────\n"
            "• adv set <nội dung>\n"
            "• adv uid add <uid>\n"
            "• adv uid remove <stt>\n"
            "• adv uid list\n"
            "• adv img add <url>\n"
            "• adv img list\n"
            "• adv img remove <stt>\n"
            "• adv send — gửi TEXT + ẢNH\n"
        ), msg_obj, tid, ttype)
        return

    # SET TEXT
    if args[1] == "set":
        write_file(FILE_TEXT, " ".join(args[2:]))
        client.replyMessage(Message(text="✔ Đã lưu nội dung quảng cáo!"), msg_obj, tid, ttype)
        return

    # UID
    if args[1] == "uid":
        uidlist = load_json(FILE_UID, [])

        if args[2] == "add":
            u = args[3]
            uidlist.append(u)
            save_json(FILE_UID, uidlist)
            client.replyMessage(Message(text=f"✔ Thêm UID {u}"), msg_obj, tid, ttype)
            return

        if args[2] == "remove":
            try:
                i = int(args[3]) - 1
                rm = uidlist.pop(i)
                save_json(FILE_UID, uidlist)
                client.replyMessage(Message(text=f"✔ Đã xóa {rm}"), msg_obj, tid, ttype)
            except:
                client.replyMessage(Message(text="⚠ Sai số thứ tự"), msg_obj, tid, ttype)
            return

        if args[2] == "list":
            if not uidlist:
                client.replyMessage(Message(text="⚠ Chưa có UID"), msg_obj, tid, ttype)
            else:
                out = "\n".join([f"{i+1}. {u}" for i, u in enumerate(uidlist)])
                client.replyMessage(Message(text="📜 UID LIST:\n"+out), msg_obj, tid, ttype)
            return

    # IMAGE
    if args[1] == "img":
        imgs = load_json(FILE_IMG, [])

        if args[2] == "add":
            imgs.append(args[3])
            save_json(FILE_IMG, imgs)
            client.replyMessage(Message(text="✔ Đã thêm ảnh"), msg_obj, tid, ttype)
            return

        if args[2] == "remove":
            try:
                i = int(args[3]) - 1
                rm = imgs.pop(i)
                save_json(FILE_IMG, imgs)
                client.replyMessage(Message(text=f"✔ Đã xóa ảnh {rm}"), msg_obj, tid, ttype)
            except:
                client.replyMessage(Message(text="⚠ Sai số thứ tự"), msg_obj, tid, ttype)
            return

        if args[2] == "list":
            if not imgs:
                client.replyMessage(Message(text="⚠ Không có ảnh"), msg_obj, tid, ttype)
            else:
                out = "\n".join([f"{i+1}. {u}" for i, u in enumerate(imgs)])
                client.replyMessage(Message(text="📸 IMAGE LIST:\n"+out), msg_obj, tid, ttype)
            return

    # SEND (TEXT + IMAGE)
    if args[1] == "send":

        text = read_file(FILE_TEXT)
        uids = load_json(FILE_UID, [])
        images = load_json(FILE_IMG, [])

        if not uids:
            client.replyMessage(Message(text="⚠ Danh sách UID trống"), msg_obj, tid, ttype)
            return

        client.replyMessage(Message(text=f"⏳ Bắt đầu gửi {len(uids)} UID…"), msg_obj, tid, ttype)

        ok = 0
        for u in uids:
            if send_adv(client, u, text, images):
                ok += 1
            time.sleep(0.5)

        client.replyMessage(Message(text=f"✔ Hoàn tất: {ok}/{len(uids)} UID"), msg_obj, tid, ttype)
        return

    client.replyMessage(Message(text="⚠ Sai cú pháp! dùng: adv help"), msg_obj, tid, ttype)


def PTA():
    return {
        "ad": handle_adv_cmd
    }
