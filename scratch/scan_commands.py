import os
import re

modules_dir = r"c:\Users\cacquoc\Downloads\dcm\modules"
commands = {}

for filename in os.listdir(modules_dir):
    if filename.endswith(".py") and filename != "__init__.py":
        filepath = os.path.join(modules_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            # Simple regex search for PTA() function
            pta_match = re.search(r"def\s+PTA\s*\([^)]*\)\s*:(.*?)(?=def|\Z)", content, re.DOTALL)
            if pta_match:
                pta_body = pta_match.group(1)
                # Find all keys registered in dict return
                dict_keys = re.findall(r"['\"]([^'\"]+)['\"]\s*:", pta_body)
                if dict_keys:
                    commands[filename] = dict_keys
                else:
                    commands[filename] = ["PTA found but no keys extracted"]
        except Exception as e:
            commands[filename] = [f"Error: {e}"]

for filename, cmds in sorted(commands.items()):
    print(f"{filename}: {cmds}")
