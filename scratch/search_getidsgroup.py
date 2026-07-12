import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

search_dirs = [
    r"c:\Users\cacquoc\Downloads\dcm",
    r"c:\Users\cacquoc\Downloads\dcm\modules",
    r"c:\Users\cacquoc\Downloads\dcm\commands"
]

for directory in search_dirs:
    # Just list files in that directory directly, do not recurse into subdirectories unless explicitly needed
    for filename in os.listdir(directory):
        if filename.endswith(".py"):
            filepath = os.path.join(directory, filename)
            if not os.path.isfile(filepath):
                continue
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if "getIDsGroup" in line:
                            print(f"{filename}:{i}: {line.strip()}")
            except Exception as e:
                pass
