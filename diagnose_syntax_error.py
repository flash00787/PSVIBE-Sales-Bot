# Fix main_menu.py - find the unterminated triple-quote
path = '/root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py'
with open(path) as f:
    lines = f.readlines()

print(f'File has {len(lines)} lines')
print(f'Line 33: {repr(lines[32])}' if len(lines) > 32 else 'Less than 33 lines')
print(f'Last 10 lines:')
for i, line in enumerate(lines[-10:]):
    print(f'  {len(lines)-10+i}: {repr(line)}')

# Check for unterminated """
in_multiline = False
for i, line in enumerate(lines):
    stripped = line.strip()
    if '"""' in stripped:
        count = stripped.count('"""')
        if count % 2 == 1:
            in_multiline = not in_multiline
            print(f'Line {i+1}: {"OPEN" if in_multiline else "CLOSE"} triple quote — {repr(stripped)}')
    
if in_multiline:
    print(f'\n⚠️  Unterminated triple quote - still open at end of file')
    
# Fix: find and close the unterminated string
# Look for a line starting with # or code after """
# The issue is the inline BTN constants - let me check what's there
for i, line in enumerate(lines[:5]):
    print(f'Line {i+1}: {repr(line)}')
