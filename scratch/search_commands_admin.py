import os
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

commands_dir = r"c:\Users\cacquoc\Downloads\dcm\commands"

for filename in os.listdir(commands_dir):
    if filename.endswith(".py"):
        filepath = os.path.join(commands_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if "ADMIN" in line or "is_allowed_author" in line:
                        print(f"{filename}:{i}: {line.strip()}")
        except Exception as e:
            pass
