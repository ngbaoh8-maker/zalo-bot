import os
import sys
import json
import subprocess
import threading
import queue

class BotRunner:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.processes = {}      # username -> Popen
        self.log_queues = {}     # username -> Queue
        self.locks = {}          # username -> Lock
        self.global_lock = threading.Lock()

    def get_lock(self, username):
        with self.global_lock:
            if username not in self.locks:
                self.locks[username] = threading.Lock()
            return self.locks[username]

    def get_log_queue(self, username):
        with self.global_lock:
            if username not in self.log_queues:
                self.log_queues[username] = queue.Queue(maxsize=1000)
            return self.log_queues[username]

    def log_message(self, username, message):
        q = self.get_log_queue(username)
        try:
            q.put_nowait(message)
        except queue.Full:
            try:
                q.get_nowait()
                q.put_nowait(message)
            except Exception:
                pass

    def update_config_files(self, username, bot_name, admin_id, prefix):
        user_dir = os.path.join(self.root_dir, 'users', username)
        os.makedirs(user_dir, exist_ok=True)
        
        # 1. Update seting.json in user's directory
        setting_path = os.path.join(user_dir, 'seting.json')
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
        
        if 'adm' not in settings:
            settings['adm'] = []
        if admin_id not in settings['adm']:
            settings['adm'].append(admin_id)

        with open(setting_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

        # 2. Compile templates to user's directory
        templates = [
            ('main.py.template', 'main.py'),
            ('PTA.py.template', 'PTA.py'),
            ('modules/AI/pro_gemini.py.template', 'modules/AI/pro_gemini.py')
        ]

        for temp_name, target_rel_path in templates:
            temp_path = os.path.join(self.root_dir, temp_name)
            target_path = os.path.join(user_dir, target_rel_path)
            
            # Ensure folder exists
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            if os.path.exists(temp_path):
                try:
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Replace {name} placeholder
                    replaced = content.replace('{name}', bot_name)
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(replaced)
                except Exception as e:
                    self.log_message(username, f"[SYSTEM ERROR] Lỗi khi tạo file {target_rel_path}: {e}\n")

    def start(self, username, bot_name, admin_id, prefix):
        lock = self.get_lock(username)
        with lock:
            if self.is_running(username):
                return False, "Bot của bạn đang chạy rồi!"

            # Update configuration and template source files in user dir
            self.update_config_files(username, bot_name, admin_id, prefix)

            self.log_message(username, "[SYSTEM] Khởi động bot...\n")
            
            python_exe = sys.executable
            user_dir = os.path.join(self.root_dir, 'users', username)
            main_py = os.path.join(user_dir, 'main.py')

            # Build isolated environment
            sub_env = os.environ.copy()
            sub_env['BOT_USER'] = username
            # Include root dir in PYTHONPATH so python can resolve global modules/zlapi
            if 'PYTHONPATH' in sub_env:
                sub_env['PYTHONPATH'] = self.root_dir + os.pathsep + sub_env['PYTHONPATH']
            else:
                sub_env['PYTHONPATH'] = self.root_dir

            try:
                # Start subprocess inside user dir
                proc = subprocess.Popen(
                    [python_exe, main_py],
                    cwd=self.root_dir,
                    env=sub_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    bufsize=1
                )
                self.processes[username] = proc

                # Start log reader thread
                threading.Thread(target=self._read_logs, args=(username, proc), daemon=True).start()
                return True, "Khởi động bot thành công!"
            except Exception as e:
                self.log_message(username, f"[SYSTEM ERROR] Không thể khởi chạy tiến trình: {e}\n")
                return False, f"Lỗi khởi chạy: {e}"

    def stop(self, username):
        lock = self.get_lock(username)
        with lock:
            if not self.is_running(username):
                return False, "Bot của bạn không chạy!"

            self.log_message(username, "[SYSTEM] Đang dừng bot...\n")
            proc = self.processes[username]
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
            except Exception as e:
                self.log_message(username, f"[SYSTEM ERROR] Không thể dừng bot: {e}\n")

            self.processes[username] = None
            self.log_message(username, "[SYSTEM] Bot đã dừng.\n")
            return True, "Dừng bot thành công!"

    def is_running(self, username):
        proc = self.processes.get(username)
        if proc is not None:
            if proc.poll() is None:
                return True
            else:
                self.processes[username] = None
        return False

    def _read_logs(self, username, proc):
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            self.log_message(username, line)
        
        proc.wait()
        lock = self.get_lock(username)
        with lock:
            if self.processes.get(username) == proc:
                self.processes[username] = None
                self.log_message(username, "[SYSTEM] Tiến trình bot kết thúc.\n")

    def get_logs(self, username):
        q = self.get_log_queue(username)
        logs = []
        while not q.empty():
            try:
                logs.append(q.get_nowait())
            except queue.Empty:
                break
        return "".join(logs)
