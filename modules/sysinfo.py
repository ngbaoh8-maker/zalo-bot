import os
import time
import platform
import shutil
import socket
import subprocess
from datetime import datetime
from zlapi.models import Message

des = {
    "version": "1.3.1",
    "credits": "ngbao",
    "description": "Hiển thị thông tin hệ thống",
    "power": "Quản trị viên Bot"
}

OWNER_ID = "833018801528797356"
OWNER_NAME = "ngbao"
START_TIME = time.time()
BOT_VERSION = "2.0.1"
MODULES_DIR = "modules"
KEY_FILE = "data/keybac.json"


# ========== HÀM HỖ TRỢ ==========
def format_duration(seconds):
    days, seconds = divmod(int(seconds), 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def get_cpu_safe():
    try:
        import psutil
        return f"{psutil.cpu_percent(interval=0.3)}%"
    except Exception:
        return "Không thể lấy CPU"

def get_ram_safe():
    try:
        import psutil
        ram = psutil.virtual_memory()
        total = round(ram.total / (1024 ** 3), 2)
        used = round(ram.used / (1024 ** 3), 2)
        return f"{used}/{total} GB ({ram.percent}%)"
    except Exception:
        return "Không thể lấy RAM"

def get_storage():
    try:
        total, used, free = shutil.disk_usage("/")
        total_gb = round(total / (1024**3), 2)
        free_gb = round(free / (1024**3), 2)
        percent = round((used / total) * 100, 1)
        return f"{free_gb}/{total_gb} GB trống ({percent}%)"
    except Exception:
        return "Không thể lấy Storage"

def get_ip_and_ping():
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        ip = "Không xác định"
    try:
        subprocess.run(["ping", "-c", "1", "8.8.8.8"], capture_output=True, timeout=3)
        ping = "OK"
    except Exception:
        ping = "N/A"
    return ip, ping

def count_modules():
    try:
        return len([f for f in os.listdir(MODULES_DIR) if f.endswith(".py")])
    except Exception:
        return 0

def count_keybac():
    try:
        import json
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return len(data.get("keybac", [])) if isinstance(data, dict) else 0
        return 0
    except Exception:
        return 0


# ========== HÀM CHÍNH ==========
def do_sysinfo(message, message_object, thread_id, thread_type, author_id, client):
    if str(author_id) != OWNER_ID:
        client.replyMessage(
            Message(text="🚫 Lệnh này chỉ dành cho chủ sở hữu bot!"),
            message_object, thread_id, thread_type, ttl=60000
        )
        return

    cpu = get_cpu_safe()
    ram = get_ram_safe()
    storage = get_storage()
    ip, ping = get_ip_and_ping()
    uptime = format_duration(time.time() - START_TIME)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sys_info = platform.uname()
    modules_count = count_modules()
    keybac_count = count_keybac()

    text = (
        f"💻 THÔNG TIN HỆ THỐNG BOT\n"
        f"──────────────────────────\n"
        f"🧠 CPU: {cpu}\n"
        f"💾 RAM: {ram}\n"
        f"🗄️ Storage: {storage}\n"
        f"🌐 IP: {ip} | Ping: {ping}\n"
        f"⏱️ Uptime: {uptime}\n"
        f"⏰ Now: {now}\n"
        f"⚙️ OS: {sys_info.system} {sys_info.release}\n"
        f"🔎 Python: {platform.python_version()}\n"
        f"🤖 Bot Version: {BOT_VERSION}\n"
        f"📨 Modules: {modules_count}\n"
        f"🔑 Key Users: {keybac_count}\n"
        f"👑 Chủ sở hữu: {OWNER_NAME} ✅\n"
        f"──────────────────────────\n"
        f"✨ Bot đang hoạt động ổn định!"
    )

    client.replyMessage(
        Message(text=text),
        message_object, thread_id, thread_type, ttl=90000
    )


def PTA():
    return {"sysif": do_sysinfo}