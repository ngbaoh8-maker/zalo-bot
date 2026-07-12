import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"c:\Users\cacquoc\Downloads\dcm\main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
    for i, line in enumerate(lines, 1):
        if "def is_allowed_author" in line:
            start = max(0, i - 2)
            end = min(len(lines), i + 8)
            for j in range(start, end):
                print(f"{j+1}: {lines[j].strip()}")
