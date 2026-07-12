from zlapi.models import *
import platform
import psutil
import time
import socket
import datetime
import sys
import os

des = {
    'version': "1.2.0",
    'credits': "ngbao",
    'description': "Ẩn",
    'power': "Admin"
}

# Thông tin bot
bot_name = "ngbao"
cre = "ngbao dthw"
start_time = time.time()

def get_uptime():
    """Tính thời gian bot hoạt động"""
    try:
        uptime_sec = int(time.time() - start_time)
        if uptime_sec < 0:
            raise ValueError("Thời gian hoạt động không thể âm")
        hours = uptime_sec // 3600
        minutes = (uptime_sec % 3600) // 60
        seconds = uptime_sec % 60
        return f"{hours}h {minutes}m {seconds}s"
    except Exception as e:
        print(f"Lỗi khi tính uptime: {e}")
        return "0h 0m 0s"

def get_system_info():
    """Lấy thông tin hệ điều hành"""
    try:
        os_name = platform.system()
        os_release = platform.release()
        os_version = platform.version()
        if not os_name:
            raise ValueError("Không thể lấy tên hệ điều hành")
        return f"{os_name} {os_release} ({os_version})"
    except Exception as e:
        print(f"Lỗi khi lấy thông tin hệ thống: {e}")
        return "Linux Unknown"

def get_cpu_info():
    """Lấy thông tin CPU với kiểm tra đặc biệt cho Termux/Android"""
    try:
        cpu_name = platform.processor()
        if not cpu_name or cpu_name == "Unknown CPU":
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'model name' in line.lower():
                            cpu_name = line.split(':')[1].strip()
                            break
                    else:
                        cpu_name = "ARM64 Processor (Termux)"
            except:
                cpu_name = "ARM64 Processor (Termux)"

        cpu_cores = psutil.cpu_count(logical=False) or 1
        cpu_threads = psutil.cpu_count(logical=True) or 1
        cpu_usage = psutil.cpu_percent(interval=0.1)
        if cpu_cores < 1 or cpu_threads < 1:
            raise ValueError("Số lõi/luồng CPU không hợp lệ")
        return f"{cpu_name}\n      📊 Cores: {cpu_cores} | Threads: {cpu_threads} | Usage: {cpu_usage}%"
    except Exception as e:
        print(f"Lỗi khi lấy thông tin CPU: {e}")
        return "ARM64 Processor (Termux)\n      📊 Cores: 1 | Threads: 1 | Usage: 0%"

def get_ram_info():
    """Lấy thông tin RAM"""
    try:
        mem = psutil.virtual_memory()
        total = round(mem.total / (1024 ** 3), 2)  # GB
        used = round(mem.used / (1024 ** 3), 2)
        available = round(mem.available / (1024 ** 3), 2)
        percent = mem.percent
        if total <= 0 or used < 0 or available < 0 or percent < 0 or percent > 100:
            raise ValueError("Giá trị RAM không hợp lệ")
        return {
            "total": total,
            "used": used,
            "available": available,
            "percent": percent
        }
    except Exception as e:
        print(f"Lỗi khi lấy thông tin RAM: {e}")
        return {
            "total": 0.0,
            "used": 0.0,
            "available": 0.0,
            "percent": 0.0
        }

def get_swap_info():
    """Lấy thông tin Swap"""
    try:
        swap = psutil.swap_memory()
        total = round(swap.total / (1024 ** 3), 2)
        used = round(swap.used / (1024 ** 3), 2)
        free = round(swap.free / (1024 ** 3), 2)
        if total < 0 or used < 0 or free < 0:
            raise ValueError("Giá trị Swap không hợp lệ")
        return {
            "total": total,
            "used": used,
            "free": free
        }
    except Exception as e:
        print(f"Lỗi khi lấy thông tin Swap: {e}")
        return {
            "total": 0.0,
            "used": 0.0,
            "free": 0.0
        }

def get_disk_info():
    """Lấy thông tin bộ nhớ với kiểm tra đặc biệt cho Termux"""
    try:
        disk_path = '/data' if 'TERMUX_VERSION' in os.environ else '/'
        disk = psutil.disk_usage(disk_path)
        total = round(disk.total / (1024 ** 3), 2)
        used = round(disk.used / (1024 ** 3), 2)
        free = round(disk.free / (1024 ** 3), 2)
        percent = disk.percent
        if total <= 0 or used < 0 or free < 0 or percent < 0 or percent > 100:
            raise ValueError("Giá trị Storage không hợp lệ")
        return f"💿 {disk_path}: {used}/{total} GB ({percent}%) - Trống: {free} GB"
    except Exception as e:
        print(f"Lỗi khi lấy thông tin Storage: {e}")
        try:
            disk = psutil.disk_usage('/')
            total = round(disk.total / (1024 ** 3), 2)
            used = round(disk.used / (1024 ** 3), 2)
            free = round(disk.free / (1024 ** 3), 2)
            percent = disk.percent
            return f"💿 /: {used}/{total} GB ({percent}%) - Trống: {free} GB"
        except:
            return "💿 /: 0/0 GB (0%) - Trống: 0 GB"

def get_process_info():
    """Lấy thông tin tiến trình bot"""
    try:
        process = psutil.Process(os.getpid())
        pid = process.pid
        ram_usage = round(process.memory_info().rss / (1024 ** 2), 2)  # MB
        cpu_usage = process.cpu_percent(interval=0.1)
        if pid <= 0:
            raise ValueError("PID không hợp lệ")
        return f"PID: {pid} | RAM: {ram_usage}MB | CPU: {cpu_usage}%"
    except Exception as e:
        print(f"Lỗi khi lấy thông tin Process: {e}")
        return "PID: 0 | RAM: 0MB | CPU: 0%"

def get_python_info():
    """Lấy thông tin Python"""
    try:
        py_version = platform.python_version()
        return f"CPython {py_version}"
    except Exception as e:
        print(f"Lỗi khi lấy thông tin Python: {e}")
        return "CPython Unknown"

def get_app_info():
    """Lấy thông tin ứng dụng chạy bot"""
    try:
        if 'TERMUX_VERSION' in os.environ:
            return "Termux"
        elif 'powershell' in sys.executable.lower() or 'cmd' in sys.executable.lower():
            return "Windows Terminal/CMD/PowerShell"
        else:
            return "Windows Terminal/CMD/PowerShell"
    except Exception as e:
        print(f"Lỗi khi lấy thông tin App: {e}")
        return "Termux"

def handle_check_command(message, message_object, thread_id, thread_type, author_id, client):
    """Xử lý lệnh chi tiết bot"""
    try:
        # Lấy thời gian hiện tại
        now = datetime.datetime.now()
        date_str = now.strftime("%A, %d/%m/%Y")
        time_str = now.strftime("%H:%M:%S")

        # Lấy thông tin hệ thống
        ram_info = get_ram_info()
        swap_info = get_swap_info()

        # Tạo nội dung thông tin
        content = f"""[ THÔNG TIN CHI TIẾT BOT ]

⏰ THỜI GIAN:
   📅 Ngày: `{date_str}`
   🕐 Giờ: `{time_str}`

🖥️ HỆ THỐNG:
   📡 {get_system_info()}
      🔧 {platform.machine()} | {platform.architecture()[0]}

💻 PHẦN CỨNG:
   📊 RAM CHI TIẾT:
   🔹 Tổng: {ram_info['total']} GB
   🔹 Đã dùng: {ram_info['used']} GB ({ram_info['percent']}%)
   🔹 Còn lại: {ram_info['available']} GB ({100 - ram_info['percent']:.1f}%)
   🔹 Free: {ram_info['available']} GB
   💫 SWAP:
   🔹 Tổng: {swap_info['total']} GB
   🔹 Đã dùng: {swap_info['used']} GB
   🔹 Còn lại: {swap_info['free']} GB
   ⚙️ CPU: `{get_cpu_info()}`
   💾 STORAGE: `{get_disk_info()}`

🐍 PYTHON:
   📦 VERSION: `{get_python_info()}`
   📲 CHẠY TRÊN: `{get_app_info()}`

🚀 BOT INFO:
   🔄 PROCESS: `{get_process_info()}`
   👑 ADMIN: `ngbao`
   🎨 CREATED BY: `ngbao 😎`
   ⏱️ BOT UPTIME: `{get_uptime()}`
"""
        client.replyMessage(Message(text=content), message_object, thread_id, thread_type)
    except Exception as e:
        print(f"Lỗi tổng khi xử lý handle_check_command: {e}")
        error_content = "Đã xảy ra lỗi khi lấy thông tin bot. Vui lòng thử lại sau."
        client.replyMessage(Message(text=error_content), message_object, thread_id, thread_type)

# ----- Thêm TQuan giống kiểu aipy -----
def PTA():
    return {
        'check': handle_check_command
    }
