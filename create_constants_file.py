# Create a shared constants file that won't cause circular imports
# Both bot/__init__.py and bot/handlers/*.py can import from this

path = '/root/Sales-Tele-Bot_refactored/bot/_constants.py'

# Only verify what's needed. If file exists, append missing ones.
import os

base_dir = '/root/Sales-Tele-Bot_refactored/bot'

# Read from __init__.py to get existing constants
init_path = os.path.join(base_dir, '__init__.py')
with open(init_path) as f:
    init_content = f.read()

# Extract BTN_ and other constant definitions
constant_lines = []
capture = False
for line in init_content.split('\n'):
    if line.strip().startswith('# =========== BTN'):
        capture = True
    if line.strip().startswith('class BotState'):
        break
    if capture:
        if line.strip().startswith('class ') or line.strip().startswith('# ====='):
            continue
        constant_lines.append(line)
    if not capture and line.strip().startswith('# ====== CONFIG'):
        capture = True
        constant_lines.append(line)

# Also add now_mmt and fetch_allowed_staff_ids
extra = [
    '\n',
    '# Functions',
    '',
]

# Check if _constants.py already exists
try:
    with open(path) as f:
        existing = f.read()
    print('_constants.py already exists, checking...')
    # Add any missing constants
    needed = constant_lines + extra
    missing = [l for l in needed if l.strip() and l.strip() not in existing]
    if missing:
        with open(path, 'a') as f:
            f.write('\n'.join(missing))
        print(f'Added {len(missing)} missing constants')
    else:
        print('All constants already in _constants.py')
except FileNotFoundError:
    # Create new file
    content = (
        '# Shared constants for PS VIBE Staff Bot\n'
        '# Imported by bot/__init__.py and bot/handlers/*.py\n'
        '# (No circular import risk since handlers don\'t import this directly)\n'
        '\n'
    )
    content += '\n'.join(constant_lines) + '\n'
    content += '\n'.join(extra) + '\n'
    
    with open(path, 'w') as f:
        f.write(content)
    print(f'CREATED _constants.py with {len(constant_lines)} constant lines')

# Now verify
with open(path) as f:
    print(f'\nFile exists: {os.path.getsize(path)} bytes')
    print('First 3 lines:', f.readline().strip())
