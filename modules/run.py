import os
import requests
from config import ADMIN
from zlapi.models import Message
import urllib.parse
import subprocess
import json
import ast
import io
import sys

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Chạy thử 1 đoạn code",
    'power': "Quản trị viên Bot"
}

def prf():
    return PREFIX

def handle_run_command(message, message_object, thread_id, thread_type, author_id, client):
    # Kiểm tra quyền từ config.ADMIN trực tiếp
    if str(author_id) not in [str(a) for a in ADMIN]:
        client.replyMessage(Message(text="• Bạn không đủ quyền hạn để sử dụng lệnh này."), message_object, thread_id, thread_type)
        return

    command = message[len(f"{prf()}run "):]

    if command.startswith("pip uninstall"):
        command += " -y"
    
    if command.startswith(("pip", "python", "node", "npm", "sudo", "ls", "cd")):
        try:
            result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = result.communicate()
            response_message = stdout if result.returncode == 0 else stderr
        except Exception as e:
            response_message = f"Có lỗi xảy ra: {str(e)}"
    else:
        try:
            output_buffer = io.StringIO()
            sys.stdout = output_buffer
            compiled_code = compile(command, '<string>', 'exec')
            local_vars = {}
            exec(compiled_code, {}, local_vars)
            sys.stdout = sys.__stdout__
            output = output_buffer.getvalue()
            output_buffer.close()
            if output:
                response_message = output
            elif local_vars:
                response_message = "\n".join(f"{k}: {v}" for k, v in local_vars.items())
            else:
                response_message = "Done!"
        except Exception as e:
            response_message = str(e)
        finally:
            sys.stdout = sys.__stdout__
    
    client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type)

def PTA():
    return {
        'run': handle_run_command
    }