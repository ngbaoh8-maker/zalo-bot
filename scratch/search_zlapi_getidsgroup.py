import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

zlapi_dir = r"c:\Users\cacquoc\Downloads\dcm\zlapi"
if os.path.exists(zlapi_dir):
    for root, dirs, files in os.walk(zlapi_dir):
        for filename in files:
            if filename.endswith(".py"):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f, 1):
                            if "getIDsGroup" in line:
                                print(f"zlapi/{filename}:{i}: {line.strip()}")
                except Exception as e:
                    pass
else:
    print("zlapi directory not found")
