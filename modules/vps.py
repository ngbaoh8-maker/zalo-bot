import os
import uuid
import json
import random
import string
import time
import threading
from zlapi.models import Message
from zlapi import ThreadType

des = {
    'version': "VIP 4.0 - FIXED",
    'credits': "ngbao",
    'description': "VPS giả lập xịn, interactive, full lệnh, VIP 4.0 - optimized",
    'power': "Quản trị viên Bot"
}

ADMIN_UID = "637876082720685615"
VPS_FILE = "vps_data.json"

# sessions: str(author_id) -> { vps_code: session_data }
sessions = {}

vps_data_lock = threading.Lock()

# --- Load / Save VPS data (thread-safe) ---
if os.path.exists(VPS_FILE):
    try:
        with open(VPS_FILE, "r") as f:
            vps_data = json.load(f)
    except Exception:
        vps_data = {}
else:
    vps_data = {}


def save_vps_data():
    with vps_data_lock:
        with open(VPS_FILE, "w") as f:
            json.dump(vps_data, f, indent=2, ensure_ascii=False)


def load_vps_data():
    global vps_data
    with vps_data_lock:
        if os.path.exists(VPS_FILE):
            try:
                with open(VPS_FILE, "r") as f:
                    vps_data = json.load(f)
            except Exception:
                vps_data = {}
        else:
            vps_data = {}

# --- Utils ---

def random_code():
    # ensure unique code
    for _ in range(10):
        code = ''.join(random.choices(string.ascii_uppercase, k=3)) + ''.join(random.choices(string.digits, k=2))
        with vps_data_lock:
            if code not in vps_data:
                return code
    # fallback to uuid fragment
    return uuid.uuid4().hex[:5].upper()


def fake_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"


def fake_os():
    return random.choice(["Ubuntu 22.04", "Debian 12", "CentOS 8", "Fedora 38", "Alpine 3.18"])


def _format_time(ts):
    if not ts:
        return "Không giới hạn"
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
    except Exception:
        return str(ts)


def create_windows10_desktop(vps_code):
    """Tạo màn hình Windows 10 mặc định cho VPS mới"""
    desktop = {
        "vps": vps_code,
        "theme": "Windows 10 Dark",
        "wallpaper": "default.jpg",
        "files": {
            "bot zalo": {
                "type": "folder",
                "content": ["config.json", "main.py", "modules", "data.db"],
                "size": "45 MB",
                "created": time.time()
            },
            "272": {
                "type": "folder",
                "content": ["anh1.jpg", "anh2.png", "doc1.txt", "data.xlsx"],
                "size": "128 MB",
                "created": time.time() - 86400
            },
            "chrome.exe": {
                "type": "app",
                "status": "closed",
                "version": "120.0.6099.110",
                "size": "85 MB"
            },
            "notepad.exe": {
                "type": "app",
                "status": "closed",
                "version": "10.0",
                "size": "2 MB"
            },
            "calculator.exe": {
                "type": "app",
                "status": "closed",
                "version": "10.2103.8.0",
                "size": "5 MB"
            },
            "cmd.exe": {
                "type": "app",
                "status": "closed",
                "version": "10.0.19041.1",
                "size": "1 MB"
            },
            "task_manager.exe": {
                "type": "app",
                "status": "closed",
                "version": "10.0.19041.1",
                "size": "3 MB"
            },
            "explorer.exe": {
                "type": "app",
                "status": "opened",
                "version": "10.0.19041.1",
                "size": "8 MB"
            }
        },
        "running_apps": [],
        "opened_files": []
    }
    return desktop


def display_windows_desktop(vps_code, desktop):
    """Hiển thị màn hình Windows 10"""
    desktop_view = f"🖥️ **MÀN HÌNH WINDOWS 10 - VPS {vps_code}**\n"
    desktop_view += "═" * 50 + "\n"
    desktop_view += "📁 **THƯ MỤC & ỨNG DỤNG:**\n\n"
    
    # Hiển thị files và apps có index
    items = list(desktop["files"].items())
    for idx, (name, info) in enumerate(items, 1):
        icon = "📁" if info["type"] == "folder" else "⚙️" if info["type"] == "app" else "📄"
        status = "🟢 ĐANG MỞ" if info.get("status") == "opened" else "🔴 ĐÓNG"
        if info["type"] == "app":
            desktop_view += f"{idx}. {icon} {name} | {status} | {info['size']}\n"
        else:
            desktop_view += f"{idx}. {icon} {name} | 📦 {info['size']} | 📊 {len(info['content'])} items\n"
    
    desktop_view += "\n📊 **ỨNG DỤNG ĐANG CHẠY:**\n"
    if desktop["running_apps"]:
        for app in desktop["running_apps"]:
            desktop_view += f"   • {app}\n"
    else:
        desktop_view += "   (Không có ứng dụng nào đang chạy)\n"
    
    desktop_view += "\n📂 **FILE ĐANG MỞ:**\n"
    if desktop["opened_files"]:
        for file in desktop["opened_files"]:
            desktop_view += f"   • {file}\n"
    else:
        desktop_view += "   (Không có file nào đang mở)\n"
    
    desktop_view += "\n" + "═" * 50 + "\n"
    desktop_view += "**LỆNH SỬ DỤNG:**\n"
    desktop_view += "• vps <tên file> start : Mở file/ứng dụng\n"
    desktop_view += "• vps <tên file> stop : Đóng file/ứng dụng\n"
    desktop_view += "• vps <số index> open : Mở file bằng index\n"
    desktop_view += "• vps desktop : Hiển thị lại màn hình\n"
    desktop_view += "• vps refresh : Làm mới màn hình\n"
    
    return desktop_view


def handle_windows_command(message, vps_code, desktop, session):
    """Xử lý lệnh Windows 10 desktop"""
    parts = message.strip().split()
    
    if len(parts) < 2:
        return display_windows_desktop(vps_code, desktop)
    
    cmd_type = parts[0].lower()
    target = parts[1].lower()
    
    # Xử lý lệnh bằng index
    if target.isdigit():
        idx = int(target) - 1
        items = list(desktop["files"].keys())
        if 0 <= idx < len(items):
            target = items[idx]
        else:
            return f"❌ Index {target} không hợp lệ. Chỉ có {len(items)} items trên desktop."
    
    if target not in desktop["files"]:
        return f"❌ File/ứng dụng '{target}' không tồn tại trên desktop."
    
    item = desktop["files"][target]
    
    if cmd_type == "vps" and len(parts) >= 3:
        action = parts[2].lower()
        
        if action == "start" or action == "open":
            # Mở file/ứng dụng
            if item["type"] == "app":
                if item["status"] == "closed":
                    item["status"] = "opened"
                    if target not in desktop["running_apps"]:
                        desktop["running_apps"].append(target)
                    return f"✅ Đã mở ứng dụng {target}"
                else:
                    return f"ℹ️ Ứng dụng {target} đã mở sẵn"
            elif item["type"] == "folder":
                # Hiển thị nội dung thư mục
                content = "\n".join([f"   • {f}" for f in item["content"]])
                return f"📁 **NỘI DUNG THƯ MỤC {target.upper()}:**\n{content}\n\n📝 Gõ 'vps {target} <tên file> open' để mở file"
            else:
                # Mở file
                if target not in desktop["opened_files"]:
                    desktop["opened_files"].append(target)
                return f"✅ Đã mở file {target}\n📄 Nội dung: Đây là nội dung giả lập của file {target}"
        
        elif action == "stop" or action == "close":
            # Đóng file/ứng dụng
            if item["type"] == "app":
                if item["status"] == "opened":
                    item["status"] = "closed"
                    if target in desktop["running_apps"]:
                        desktop["running_apps"].remove(target)
                    return f"✅ Đã đóng ứng dụng {target}"
                else:
                    return f"ℹ️ Ứng dụng {target} đã đóng sẵn"
            else:
                if target in desktop["opened_files"]:
                    desktop["opened_files"].remove(target)
                    return f"✅ Đã đóng file {target}"
                else:
                    return f"ℹ️ File {target} chưa được mở"
    
    elif cmd_type == "vps" and parts[1] == "desktop":
        return display_windows_desktop(vps_code, desktop)
    
    elif cmd_type == "vps" and parts[1] == "refresh":
        return display_windows_desktop(vps_code, desktop)
    
    return display_windows_desktop(vps_code, desktop)


def fake_shell_output(cmd, session):
    # session: {cwd, fs, login_time, history, windows_desktop}
    fs = session.get("fs", {"/": ["home", "var", "tmp"]})
    current = session.get("cwd", "/")
    cmd = cmd.strip()
    if not cmd:
        return ""
    session.setdefault("history", []).append(cmd)
    parts = cmd.split()
    base = parts[0]

    if base == "pwd":
        return current
    elif base == "ls":
        return "  ".join(fs.get(current, []))
    elif base == "cd":
        if len(parts) < 2:
            return "Bạn phải nhập thư mục"
        dest = parts[1]
        if dest == "..":
            if current != "/":
                current = "/".join(current.rstrip("/").split("/")[:-1]) or "/"
        else:
            if dest.startswith("/"):
                target = dest
            else:
                target = current.rstrip("/") + "/" + dest if current != "/" else "/" + dest
            if target in fs:
                current = target
            else:
                return f"Thư mục {dest} không tồn tại"
        session["cwd"] = current
        return ""
    elif base == "mkdir":
        if len(parts) < 2:
            return "Bạn phải nhập tên thư mục"
        newdir = current.rstrip("/") + "/" + parts[1] if current != "/" else "/" + parts[1]
        if newdir in fs:
            return "Thư mục đã tồn tại"
        fs[newdir] = []
        session["fs"] = fs
        return f"Tạo thư mục {parts[1]} thành công"
    elif base == "cat":
        return "Fake file content: đây là nội dung giả lập."
    elif base == "status":
        cpu = random.randint(1, 100)
        ram = random.randint(1, 100)
        return f"CPU Usage: {cpu}%\nRAM Usage: {ram}%"
    elif base == "history":
        hist = session.get("history", [])
        return "\n".join(f"{i+1}. {h}" for i, h in enumerate(hist)) if hist else "Không có lịch sử"
    elif base == "vps" and len(parts) > 1:
        # Chuyển lệnh Windows desktop
        if "windows_desktop" in session:
            return handle_windows_command(cmd, session.get("vps_code", ""), session["windows_desktop"], session)
        else:
            return "❌ Windows desktop chưa được khởi động. Hãy login lại VPS."
    else:
        return f"Lệnh không hợp lệ: {cmd}"


# --- VPS Commands ---

def handle_vps_command(message, message_object, thread_id, thread_type, author_id, client):
    global sessions, vps_data

    # normalize author id to str for keys
    author_id = str(author_id)

    # reload latest data to avoid stale read (cheap, safe)
    load_vps_data()

    # --- Auto-expiry check: khóa VPS đã hết hạn ---
    now = time.time()
    changed = False
    with vps_data_lock:
        for code, v in list(vps_data.items()):
            if v.get("expires") and v["expires"] != None and now > v["expires"]:
                if not v.get("locked", False):
                    v["locked"] = True
                    changed = True
    if changed:
        save_vps_data()

    parts = message.strip().split()
    args = parts[1:]

    if not args:
        reply = "📌 Lệnh VPS:\n"
        reply += ".vps create <tên VPS>\n.vps list\n.vps my\n.vps duyet <mã>\n.vps lock <mã>\n.vps unlock <mã>\n.vps giahan <mã> <thời gian>\n.vps info <mã>\n.vps login <mã> <pass>\n.vps logout [<mã>]\n"
        reply += "(Trong session shell: cd, ls, pwd, mkdir, cat, status, history)\n"
        reply += "(Trong Windows desktop: vps <tên> start/stop, vps <index> open, vps desktop, vps refresh)\n"
        client.sendMessage(Message(text=reply), thread_id, thread_type)
        return

    cmd = args[0].lower()

    # --- CREATE VPS ---
    if cmd == "create":
        if len(args) < 2:
            client.sendMessage(Message(text="❌ Vui lòng nhập tên VPS."), thread_id, thread_type)
            return
        vps_name = args[1]
        code = random_code()
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        vps = {
            "name": vps_name,
            "code": code,
            "password": password,
            "owner": author_id,
            "locked": False,
            "expires": None,
            "cpu": f"{random.randint(1,8)} vCPU",
            "ram": f"{random.randint(2,32)} GB",
            "disk": f"{random.randint(20,500)} GB",
            "os": "Windows 10 Pro",
            "ip": fake_ip(),
            "created": time.time(),
            "windows_enabled": True
        }
        with vps_data_lock:
            vps_data[code] = vps
            save_vps_data()
        
        # Tạo desktop Windows 10 mặc định
        desktop = create_windows10_desktop(code)
        
        reply = f"✅ VPS {vps_name} đã tạo!\n"
        reply += f"🆔 Mã: {code}\n"
        reply += f"🔑 Mật khẩu: {password}\n"
        reply += f"🖥️ Hệ điều hành: Windows 10 Pro\n"
        reply += f"📊 CPU: {vps['cpu']} | RAM: {vps['ram']} | Disk: {vps['disk']}\n"
        reply += f"🌐 IP: {vps['ip']}\n\n"
        reply += "🚀 **VPS ĐÃ TỰ ĐỘNG KHỞI ĐỘNG WINDOWS 10**\n"
        reply += "Gõ '.vps login <mã> <pass>' để bắt đầu sử dụng!\n"
        
        client.sendMessage(Message(text=reply), thread_id, thread_type)
        return

    # --- LIST VPS ---
    if cmd == "list":
        with vps_data_lock:
            if not vps_data:
                client.sendMessage(Message(text="📄 Không có VPS nào."), thread_id, thread_type)
                return
            reply = "📄 Danh sách VPS đang hoạt động:\n"
            for v in vps_data.values():
                reply += f"- {v['name']} ({v['code']}) | OS: {v['os']} | Owner: {v['owner']} | Locked: {v['locked']} | Expires: {_format_time(v.get('expires'))}\n"
        client.sendMessage(Message(text=reply), thread_id, thread_type)
        return

    # --- MY VPS ---
    if cmd == "my":
        reply = f"📦 VPS của bạn ({author_id}):\n"
        found = False
        with vps_data_lock:
            for v in vps_data.values():
                if v.get("owner") == author_id:
                    os_info = v.get('os', 'Unknown')
                    reply += f"- {v['name']} ({v['code']}) | OS: {os_info} | Locked: {v['locked']} | Expires: {_format_time(v.get('expires'))}\n"
                    found = True
        if not found:
            reply += "Bạn chưa có VPS nào."
        client.sendMessage(Message(text=reply), thread_id, thread_type)
        return

    # --- DUYET VPS (admin) ---
    if cmd == "duyet":
        if author_id != ADMIN_UID:
            client.sendMessage(Message(text="❌ Chỉ admin mới thực hiện được lệnh này"), thread_id, thread_type)
            return
        if len(args) < 2:
            client.sendMessage(Message(text="❌ Nhập mã VPS cần duyệt"), thread_id, thread_type)
            return
        code = args[1]
        with vps_data_lock:
            if code not in vps_data:
                client.sendMessage(Message(text="❌ VPS không tồn tại"), thread_id, thread_type)
                return
            vps_data[code]["locked"] = False
            save_vps_data()
        client.sendMessage(Message(text=f"✅ VPS {code} đã được duyệt, có thể sử dụng"), thread_id, thread_type)
        return

    # --- LOCK VPS (admin) ---
    if cmd == "lock":
        if author_id != ADMIN_UID:
            client.sendMessage(Message(text="❌ Chỉ admin mới thực hiện được lệnh này"), thread_id, thread_type)
            return
        if len(args) < 2:
            client.sendMessage(Message(text="❌ Nhập mã VPS cần khóa"), thread_id, thread_type)
            return
        code = args[1]
        with vps_data_lock:
            if code not in vps_data:
                client.sendMessage(Message(text="❌ VPS không tồn tại"), thread_id, thread_type)
                return
            vps_data[code]["locked"] = True
            save_vps_data()
        client.sendMessage(Message(text=f"🔒 VPS {code} đã bị khóa"), thread_id, thread_type)
        return

    # --- UNLOCK VPS (admin) ---
    if cmd == "unlock":
        if author_id != ADMIN_UID:
            client.sendMessage(Message(text="❌ Chỉ admin mới thực hiện được lệnh này"), thread_id, thread_type)
            return
        if len(args) < 2:
            client.sendMessage(Message(text="❌ Nhập mã VPS cần mở khóa"), thread_id, thread_type)
            return
        code = args[1]
        with vps_data_lock:
            if code not in vps_data:
                client.sendMessage(Message(text="❌ VPS không tồn tại"), thread_id, thread_type)
                return
            vps_data[code]["locked"] = False
            save_vps_data()
        client.sendMessage(Message(text=f"✅ VPS {code} đã được mở khóa"), thread_id, thread_type)
        return

    # --- GIA HẠN VPS (admin) ---
    if cmd == "giahan":
        if author_id != ADMIN_UID:
            client.sendMessage(Message(text="❌ Chỉ admin mới thực hiện được lệnh này"), thread_id, thread_type)
            return
        if len(args) < 3:
            client.sendMessage(Message(text="❌ Sử dụng: .vps giahan <mã> <10s/5m/1h/1d>"), thread_id, thread_type)
            return
        code = args[1]
        t = args[2]
        with vps_data_lock:
            if code not in vps_data:
                client.sendMessage(Message(text="❌ VPS không tồn tại"), thread_id, thread_type)
                return
            now = time.time()
            sec = 0
            try:
                if t.endswith("s"):
                    sec = int(t[:-1])
                elif t.endswith("m"):
                    sec = int(t[:-1]) * 60
                elif t.endswith("h"):
                    sec = int(t[:-1]) * 3600
                elif t.endswith("d"):
                    sec = int(t[:-1]) * 86400
                else:
                    sec = int(t)
            except Exception:
                client.sendMessage(Message(text="❌ Thời gian không hợp lệ."), thread_id, thread_type)
                return
            vps_data[code]["expires"] = now + sec
            save_vps_data()
        client.sendMessage(Message(text=f"✅ VPS {code} đã được gia hạn thêm {t}. Hết hạn: {_format_time(vps_data[code].get('expires'))}"), thread_id, thread_type)
        return

    # --- INFO VPS ---
    if cmd == "info":
        if len(args) < 2:
            client.sendMessage(Message(text="❌ Nhập mã VPS cần xem"), thread_id, thread_type)
            return
        code = args[1]
        with vps_data_lock:
            if code not in vps_data:
                client.sendMessage(Message(text="❌ VPS không tồn tại"), thread_id, thread_type)
                return
            v = vps_data[code]
            if author_id == ADMIN_UID:
                reply = f"📊 Info VPS {code} (Admin view):\n"
                for k, val in v.items():
                    if k == "expires":
                        reply += f"{k}: {_format_time(val)}\n"
                    else:
                        reply += f"{k}: {val}\n"
            else:
                reply = f"📊 Info VPS {code}:\n"
                reply += f"Name: {v['name']}\n"
                reply += f"Code: {v['code']}\n"
                reply += f"Owner: {v['owner']}\n"
                reply += f"OS: {v['os']}\n"
                reply += f"CPU: {v['cpu']}\n"
                reply += f"RAM: {v['ram']}\n"
                reply += f"Disk: {v['disk']}\n"
                reply += f"IP: {v['ip']}\n"
                reply += f"Locked: {v['locked']}\n"
                reply += f"Expires: {_format_time(v.get('expires'))}\n"
        client.sendMessage(Message(text=reply), thread_id, thread_type)
        return

    # --- LOGIN VPS ---
    if cmd == "login":
        if len(args) < 3:
            client.sendMessage(Message(text="❌ Sử dụng: .vps login <mã> <pass>"), thread_id, thread_type)
            return
        code = args[1]
        password = args[2]
        with vps_data_lock:
            if code not in vps_data:
                client.sendMessage(Message(text="❌ VPS không tồn tại"), thread_id, thread_type)
                return
            v = vps_data[code]
            if v.get("locked"):
                client.sendMessage(Message(text="❌ VPS đang bị khóa"), thread_id, thread_type)
                return
            if v.get("password") != password:
                client.sendMessage(Message(text="❌ Sai mật khẩu VPS"), thread_id, thread_type)
                return
        
        # Tạo session với Windows desktop
        sessions.setdefault(author_id, {})
        
        # Tạo desktop Windows 10
        desktop = create_windows10_desktop(code)
        
        sessions[author_id][code] = {
            "cwd": "/", 
            "fs": {"/": ["home", "var", "tmp"]}, 
            "login_time": time.time(), 
            "history": [],
            "windows_desktop": desktop,
            "vps_code": code
        }
        
        # Hiển thị màn hình Windows 10 sau khi login
        desktop_view = display_windows_desktop(code, desktop)
        welcome_msg = f"✅ Đăng nhập thành công VPS {code}!\n"
        welcome_msg += f"🖥️ Hệ điều hành: {v.get('os', 'Windows 10 Pro')}\n"
        welcome_msg += f"🌐 IP: {v.get('ip', fake_ip())}\n\n"
        welcome_msg += desktop_view
        
        client.sendMessage(Message(text=welcome_msg), thread_id, thread_type)
        return

    # --- LOGOUT VPS ---
    if cmd == "logout":
        # optional .vps logout <code> to logout a specific VPS
        if len(args) >= 2:
            code = args[1]
            if author_id in sessions and code in sessions[author_id]:
                del sessions[author_id][code]
                if not sessions[author_id]:
                    del sessions[author_id]
                client.sendMessage(Message(text=f"✅ Đã thoát VPS {code}."), thread_id, thread_type)
            else:
                client.sendMessage(Message(text="⚠️ Bạn chưa login VPS này."), thread_id, thread_type)
            return
        # otherwise logout from all or first session
        if author_id in sessions:
            del sessions[author_id]
            client.sendMessage(Message(text="✅ Đã thoát khỏi tất cả VPS session."), thread_id, thread_type)
        else:
            client.sendMessage(Message(text="⚠️ Bạn không có session VPS nào đang hoạt động."), thread_id, thread_type)
        return

    # --- SHELL INTERACTIVE ---
    user_sessions = sessions.get(author_id, {})
    if user_sessions:
        # lấy VPS đầu tiên đang login (giữ hành vi cũ)
        code = list(user_sessions.keys())[0]
        session = user_sessions[code]
        
        # Kiểm tra xem message có phải là lệnh Windows desktop không
        if message.lower().startswith("vps ") and len(message.split()) > 1:
            # Đây là lệnh Windows desktop
            output = handle_windows_command(message, code, session.get("windows_desktop", create_windows10_desktop(code)), session)
        else:
            # Lệnh shell thông thường
            output = fake_shell_output(message, session)
        
        client.sendMessage(Message(text=f"💻 [{code}]: {output}"), thread_id, thread_type)
        return

    client.sendMessage(Message(text="❌ Lệnh không hợp lệ hoặc bạn chưa login VPS. Gõ .vps để xem hướng dẫn."), thread_id, thread_type)


# --- Export ---

def PTA():
    return {
        'vps': handle_vps_command,
    }
[file content end]