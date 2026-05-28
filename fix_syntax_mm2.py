# Read main_menu.py and fix the orphaned triple-quote
path = '/root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py'
with open(path) as f:
    content = f.read()

lines = content.split('\n')

# Find ALL triple-quote occurrences
print('Triple quotes found:')
for i, line in enumerate(lines):
    if '"""' in line:
        print(f'  Line {i+1}: {repr(line)}')

# The fix: remove all orphaned triple quotes (they're from original docstrings that got displaced)
new_lines = [l for l in lines if '"""' not in l or l.strip() in ('"""', "'''")]
# More precisely: remove lines that are ONLY triple quotes
import re
new_lines = []
for line in lines:
    stripped = line.strip()
    # Remove lines that are ONLY """ or ''' (orphaned docstring markers)
    if re.match(r'^["\']{3}$', stripped):
        continue
    new_lines.append(line)

result = '\n'.join(new_lines) + '\n'

try:
    compile(result, 'main_menu.py', 'exec')
    print('✅ Syntax check PASSED')
except SyntaxError as e:
    print(f'❌ Still has syntax error: {e}')
    # Show context around error line
    if e.lineno:
        start = max(0, e.lineno - 3)
        end = min(len(new_lines), e.lineno + 2)
        for i in range(start, end):
            marker = '>>>' if i == e.lineno - 1 else '   '
            print(f'{marker} {i+1}: {repr(new_lines[i])}')

with open(path, 'w') as f:
    f.write(result)
print(f'✅ Written: {len(new_lines)} lines')
