with open('zlapi/_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def print_func_at_line(line_num):
    for i in range(line_num - 1, 0, -1):
        if lines[i].strip().startswith('def '):
            print(f"Line {line_num} belongs to: {lines[i].strip()} (starts at line {i+1})")
            return
print_func_at_line(3820)
print_func_at_line(3899)
print_func_at_line(5279)
