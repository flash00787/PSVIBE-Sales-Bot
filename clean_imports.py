path = '/root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py'
with open(path) as f:
    lines = f.readlines()

# Remove any duplicate 'from bot import *' lines
new_lines = []
for line in lines:
    if line.strip() == 'from bot import *':
        continue
    new_lines.append(line)

with open(path, 'w') as f:
    f.writelines(new_lines)

print('DONE: removed duplicate from bot import *')
print('---')
for i, line in enumerate(new_lines[:5]):
    print(f'{i}: {line.strip()}')
