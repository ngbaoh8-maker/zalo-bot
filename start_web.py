import os
import sys

# Configure UTF-8 encoding for standard streams
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import subprocess
import webbrowser
import time

def install_dependencies():
    print("[SYSTEM] Dang kiem tra moi truong cai dat...")
    requirements_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')
    if not os.path.exists(requirements_file):
        print("[SYSTEM] Khong tim thay file requirements.txt!")
        return

    # Check and install
    print("[SYSTEM] Dang cai dat cac thu vien can thiet tu requirements.txt...")
    python_exe = sys.executable
    try:
        # Run pip install
        subprocess.check_call([python_exe, "-m", "pip", "install", "-r", requirements_file])
        print("[SYSTEM] Cai dat moi truong hoan tat thanh cong!")
    except subprocess.CalledProcessError as e:
        print(f"[SYSTEM ERROR] Co loi khi cai dat thu vien: {e}")
        print("[SYSTEM] Dang thu cai dat cac thu vien co ban...")
        try:
            subprocess.check_call([python_exe, "-m", "pip", "install", "Flask", "requests", "pillow", "psutil"])
        except Exception as ex:
            print(f"[SYSTEM ERROR] Khong the cai dat cac thu vien co ban: {ex}")

def start_server():
    server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_manager', 'server.py')
    if not os.path.exists(server_script):
        print(f"[SYSTEM ERROR] Khong tim thay file chay server: {server_script}")
        return

    print("[SYSTEM] Dang khoi dong may chu Web Manager...")
    python_exe = sys.executable
    
    # Auto open browser after 2.5 seconds
    def open_browser():
        time.sleep(2.5)
        print("[SYSTEM] Dang mo trinh duyet quan ly bot...")
        webbrowser.open("http://localhost:5050")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Start the server process
    try:
        subprocess.run([python_exe, server_script])
    except KeyboardInterrupt:
        print("\n[SYSTEM] Da dung may chu Web Manager.")

if __name__ == "__main__":
    # Ensure correct working directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Install all dependencies
    install_dependencies()
    
    # 2. Start Flask Server and open browser
    start_server()
