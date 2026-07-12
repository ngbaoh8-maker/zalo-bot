with open(r"c:\Users\cacquoc\Downloads\dcm\main.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if "ADMIN" in line:
            print(f"{i}: {line.strip()}")
