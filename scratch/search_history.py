content = open('zlapi/_client.py', 'r', encoding='utf-8').read()
import re
for m in re.findall(r'https?://[^\s"\'()]+/cm/[^\s"\'()]*', content):
    print(m)
