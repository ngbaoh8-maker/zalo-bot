import re
content = open('zlapi/_client.py', 'r', encoding='utf-8').read()
urls = re.findall(r'https?://[^\s"\'()]+', content)
for u in sorted(list(set(urls))):
    print(u)
