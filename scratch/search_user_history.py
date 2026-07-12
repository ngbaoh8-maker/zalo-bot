with open('zlapi/_client.py', 'r', encoding='utf-8') as f:
    content = f.read()
import re
for m in re.findall(r'def get\w*\(.*', content):
    print(m)
