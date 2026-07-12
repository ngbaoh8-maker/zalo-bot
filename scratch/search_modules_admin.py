import os
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

modules_dir = r"c:\Users\cacquoc\Downloads\dcm\modules"

for filename in os.listdir(modules_dir):
    if filename.endswith(".py"):
        filepath = os.path.join(modules_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if "ADMIN" in line:
                        print(f"{filename}:{i}: {line.strip()}")
        except Exception as e:
            pass
