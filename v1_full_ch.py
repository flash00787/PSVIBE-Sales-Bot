with open('/root/Sales-Tele-Bot/main.py.bak.phase4') as f:
    v1_text = f.read()

idx = v1_text.index('ConversationHandler(')

# Find matching closing paren properly
depth = 1
i = idx + len('ConversationHandler(')
while depth > 0 and i < len(v1_text):
    if v1_text[i] == '(':
        depth += 1
    elif v1_text[i] == ')':
        depth -= 1
    i += 1

ch_text = v1_text[idx:i]
print(f'ConversationHandler: {len(ch_text)} chars')
print('=' * 60)
print(ch_text[:3000])
if len(ch_text) > 3000:
    print('\n... (truncated) ...')
print('=' * 60)
