with open('zlapi/_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('zlapi/_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def print_function(func_name):
    start = -1
    for idx, line in enumerate(lines):
        if line.strip().startswith(f"def {func_name}("):
            start = idx
            break
    if start == -1:
        print(f"Function {func_name} not found")
        return
    
    print(f"--- {func_name} ---")
    indent = None
    for idx in range(start, len(lines)):
        line = lines[idx]
        if indent is None:
            indent = len(line) - len(line.lstrip())
        elif line.strip() and not line.startswith(" " * (indent + 1)) and line.strip().startswith("def "):
            break
        print(f"{idx+1}: {line}", end="")

print_function("sendBusinessCard")










