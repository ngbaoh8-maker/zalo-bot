import os
import sys
import json
import subprocess
import threading
import queue

class BotRunner:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.process = None
        self.log_queue = queue.Queue(maxsize=1000)
        self.lock = threading.Lock()
        self.is_running_status = False

    def update_config_files(self, bot_name, admin_id, prefix):
        # 1. Update seting.json
        setting_path = os.path.join(self.root_dir, 'seting.json')
        settings = {}
        if os.path.exists(setting_path):
            try:
                with open(setting_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except Exception:
                pass

        settings['name_bot'] = bot_name
        settings['admin'] = admin_id
        settings['prefix'] = prefix
        
        # update adm list to include admin_id if not present
        if 'adm' not in settings:
            settings['adm'] = []
        if admin_id not in settings['adm']:
            settings['adm'].append(admin_id)

        with open(setting_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

        # 2. Template replacements
        templates = [
            ('main.py.template', 'main.py'),
            ('PTA.py.template', 'PTA.py'),
            ('modules/AI/pro_gemini.py.template', 'modules/AI/pro_gemini.py')
        ]

        for temp_name, target_name in templates:
            temp_path = os.path.join(self.root_dir, temp_name)
            target_path = os.path.join(self.root_dir, target_name)
            if os.path.exists(temp_path):
                try:
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Replace {name} placeholder
                    replaced = content.replace('{name}', bot_name)
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(replaced)
                except Exception as e:
                    self.log_message(f"[SYSTEM ERROR] Lỗi khi tạo file {target_name}: {e}\n")

    def log_message(self, message):
        try:
            self.log_queue.put_nowait(message)
        except queue.Full:
            try:
                self.log_queue.get_nowait()
                self.log_queue.put_nowait(message)
            except Exception:
                pass

    def start(self, bot_name, admin_id, prefix):
        with self.lock:
            if self.is_running():
                return False, "Bot đang chạy rồi!"

            # Update configuration and source files
            self.update_config_files(bot_name, admin_id, prefix)

            self.log_message("[SYSTEM] Khởi động bot...\n")
            
            # Start subprocess
            # Use same python executable running the web manager
            python_exe = sys.executable
            main_py = os.path.join(self.root_dir, 'main.py')

            # Run in the root directory of the bot
            self.process = subprocess.Popen(
                [python_exe, main_py],
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            self.is_running_status = True

            # Start thread to read logs
            threading.Thread(target=self._read_logs, daemon=True).start()
            return True, "Khởi động bot thành công!"

    def stop(self):
        with self.lock:
            if not self.is_running():
                return False, "Bot không chạy!"

            self.log_message("[SYSTEM] Đang dừng bot...\n")
            try:
                # Terminate subprocess
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            except Exception as e:
                self.log_message(f"[SYSTEM ERROR] Không thể dừng bot: {e}\n")

            self.process = None
            self.is_running_status = False
            self.log_message("[SYSTEM] Bot đã dừng.\n")
            return True, "Dừng bot thành công!"

    def is_running(self):
        if self.process is not None:
            # Check if process is still alive
            if self.process.poll() is None:
                return True
            else:
                self.process = None
                self.is_running_status = False
        return False

    def _read_logs(self):
        proc = self.process
        if not proc:
            return
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            self.log_message(line)
        
        proc.wait()
        with self.lock:
            if self.process == proc:
                self.process = None
                self.is_running_status = False
                self.log_message("[SYSTEM] Tiến trình bot kết thúc.\n")

    def get_logs(self):
        logs = []
        while not self.log_queue.empty():
            try:
                logs.append(self.log_queue.get_nowait())
            except queue.Empty:
                break
        return "".join(logs)
