# Find ALL ConversationHandler instances in V.1
with open('/root/Sales-Tele-Bot/main.py.bak.phase4') as f:
    v1_text = f.read()

import re

# Find all ConversationHandler definitions
indices = [m.start() for m in re.finditer(r'ConversationHandler\(', v1_text)]
print(f'Found {len(indices)} ConversationHandler instances')

for idx in indices[:3]:  # Check first 3
    # Show context around it
    start = max(0, idx - 200)
    end = min(len(v1_text), idx + 500)
    context = v1_text[start:end]
    print(f'\n--- Context at pos {idx} ---')
    print(context)
    print('---')
