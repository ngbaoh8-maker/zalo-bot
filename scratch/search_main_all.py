import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"c:\Users\cacquoc\Downloads\dcm\main.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if "all" in line.lower() and "command" in line.lower():
            print(f"{i}: {line.strip()}")
