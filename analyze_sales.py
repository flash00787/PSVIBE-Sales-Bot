import re

with open('/root/Sales-Tele-Bot_refactored/bot/handlers/sales.py') as f:
    content = f.read()

start = content.find('async def _sale_bg')
if start == -1:
    print('_sale_bg NOT FOUND')
    exit()
    
body = content[start:]
end = len(body)
for m in re.finditer(r'\n(async )?def ', body):
    if m.start() > 0:
        end = m.start()
        break
sale_bg = body[:end]

base_ln = content[:start].count('\n') + 1

print('=== STATE RETURNS ===')
for m in re.finditer(r'return\s+([A-Z_]+)', sale_bg):
    ln = base_ln + content[start:start+m.start()].count('\n')
    print(f'Line {ln}: return {m.group(1)}')

print('=== SHEET OPERATIONS ===')
for m in re.finditer(r'(?:worksheet|sheet)\.(batch_update|append_row|update_cell|col_values|update)\s*\(', sale_bg):
    ln = base_ln + content[start:start+m.start()].count('\n')
    depth = 0
    for i in range(m.end(), len(sale_bg)):
        if sale_bg[i] == '(': depth += 1
        elif sale_bg[i] == ')': depth -= 1
        if depth == 0:
            full_call = sale_bg[m.start():i+1].replace('\n', ' ').strip()
            print(f'Line {ln}: {full_call[:400]}')
            break

print('=== COLUMN REFERENCES IN RANGES ===')
for m in re.finditer(r"'([A-Z]+\d*(?::[A-Z]+\d*)?)'", sale_bg):
    ln = base_ln + content[start:start+m.start()].count('\n')
    ref = m.group(1)
    if ref in ['A','B','C','D','E','F','G','H','I','J','K','L','M']:
        continue
    print(f'Line {ln}: {ref}')

print('=== CONDITION BRANCHES ===')
for m in re.finditer(r'if\s+([^:]+):', sale_bg):
    ln = base_ln + content[start:start+m.start()].count('\n')
    cond = m.group(1).strip()
    print(f'Line {ln}: if {cond}')

print('=== VARIABLES WRITTEN TO SHEET ===')
for m in re.finditer(r'append_row\(', sale_bg):
    ln = base_ln + content[start:start+m.start()].count('\n')
    depth = 0
    for i in range(m.end(), len(sale_bg)):
        if sale_bg[i] == '(': depth += 1
        elif sale_bg[i] == ')': depth -= 1
        if depth == 0:
            ctx = sale_bg[m.start():i+1].replace('\n', ' ').strip()
            print(f'Line {ln}: {ctx[:500]}')
            break

print('=== WORKSHEET NAMES USED ===')
for m in re.finditer(r'(?:get_worksheet|worksheet)\s*\([^)]*\)', sale_bg):
    ln = base_ln + content[start:start+m.start()].count('\n')
    print(f'Line {ln}: {m.group()[:200]}')
