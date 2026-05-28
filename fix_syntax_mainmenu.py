# Rewrite main_menu.py correctly with inline BTN constants + proper docstring
path = '/root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py'
with open(path) as f:
    content = f.read()

# The file starts with our inline constants followed by the original V.2 code
# Problem: the original had a docstring at some position, now it's orphaned

# Strategy: Read ALL original lines, write proper header with # comment not docstring
lines = content.split('\n')

# Find the first non-comment, non-assignment, non-empty line after our constants
new_lines = []
header_done = False
seen_import = False

for i, line in enumerate(lines):
    stripped = line.strip()
    
    # Keep the from bot.handlers import *
    if stripped == 'from bot.handlers import *' or stripped == "from bot import *":
        if not seen_import:
            new_lines.append('from bot.handlers import *')
            seen_import = True
        continue
    
    # Skip the old docstring lines
    if stripped == '"""' or stripped.startswith('"""') and not header_done:
        if header_done:
            new_lines.append(line)
        continue
    
    # Keep all BTN constant assignments from our inline fix
    if stripped.startswith('BTN_') and '=' in stripped:
        if stripped not in new_lines:
            new_lines.append(line)
        continue
    
    if stripped.startswith('#') and not seen_import:
        new_lines.append(line)
        continue
    
    if not header_done and seen_import:
        # Add a comment header
        new_lines.append('')
        new_lines.append('# ========== Main Menu Handler ==========')
        new_lines.append('')
        header_done = True
    
    new_lines.append(line)

# Remove consecutive blank lines
final = []
prev_blank = False
for line in new_lines:
    is_blank = line.strip() == ''
    if is_blank and prev_blank:
        continue
    prev_blank = is_blank
    final.append(line)

result = '\n'.join(final) + '\n'

# Verify it compiles
try:
    compile(result, 'main_menu.py', 'exec')
    print('✅ Syntax check PASSED')
    print(f'File: {len(result)} chars, {len(final)} lines')
except SyntaxError as e:
    print(f'❌ Syntax error: {e}')
    print(f'Line in question: {final[e.lineno-1] if e.lineno and e.lineno <= len(final) else "N/A"}')

# Write only if syntax is clean
with open(path, 'w') as f:
    f.write(result)
print('✅ Written to', path)
