const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  const cmds = `
echo "=== Fix remaining orphan import in __init__.py ==="
python3 -c "
path = '/root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py'
with open(path) as f: lines = f.readlines()
print('First 5 lines before fix:')
for l in lines[:5]: print(' ', repr(l))
# Check if first non-empty line is still an import (not docstring)
trimmed = [l for l in lines if l.strip()]
if trimmed and trimmed[0].startswith('from ') or trimmed[0].startswith('import '):
    # Strip all leading import lines before the docstring
    cut = 0
    for i, l in enumerate(lines):
        if l.strip().startswith('\"\"\"') or l.strip().startswith(\"'\"'\"'\"):
            cut = i
            break
    print(f'Removing {cut} leading lines before docstring')
    lines = lines[cut:]
    with open(path, 'w') as f: f.writelines(lines)
print('First 5 lines after fix:')
for l in lines[:5]: print(' ', repr(l))
"

echo ""
echo "=== Verify imports work in staging ==="
cd /root/staging/bot_src && python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from bot.handlers.main_menu import show_main_menu, step_main_menu
    print('✅ main_menu imports OK')
except Exception as e:
    print(f'❌ main_menu import FAILED: {e}')

try:
    from bot.handlers import *
    print('✅ handlers __init__ imports OK')
except Exception as e:
    print(f'❌ handlers __init__ FAILED: {e}')

try:
    from bot import main
    print('✅ bot main import OK')
except Exception as e:
    print(f'❌ bot import FAILED: {e}')
" 2>&1

echo ""
echo "=== Verify imports work in refactored ==="
cd /root/Sales-Tele-Bot_refactored && python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from bot.handlers.main_menu import show_main_menu, step_main_menu
    print('✅ main_menu imports OK')
except Exception as e:
    print(f'❌ main_menu import FAILED: {e}')

try:
    from bot.handlers import *
    print('✅ handlers __init__ imports OK')
except Exception as e:
    print(f'❌ handlers __init__ FAILED: {e}')

try:
    from bot import main
    print('✅ bot main import OK')
except Exception as e:
    print(f'❌ bot import FAILED: {e}')
" 2>&1
`;
  conn.exec(cmds, (err, stream) => {
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => { console.log(out); conn.end(); process.exit(0); });
  });
}).connect({
  host: '167.71.196.120',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
