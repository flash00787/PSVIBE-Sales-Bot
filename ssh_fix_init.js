const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  // Write fix script to VPS
  const script = `
path = '/root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py'
with open(path) as f:
    lines = f.readlines()

print('First 5 lines before fix:')
for i, l in enumerate(lines[:5]):
    print(f'  {i}: {repr(l)}')

# Find the docstring line and remove everything before it
cut = 0
for i, l in enumerate(lines):
    stripped = l.strip()
    if stripped.startswith('"""') or stripped.startswith("'''"):
        cut = i
        break

print(f'Removing {cut} leading lines before docstring')
if cut > 0:
    lines = lines[cut:]
    with open(path, 'w') as f:
        f.writelines(lines)

print('First 5 lines after fix:')
for i, l in enumerate(lines[:5]):
    print(f'  {i}: {repr(l)}')
`;
  // Execute the fix + verification
  const cmds = `python3 << 'PYEOF'
${script}
PYEOF

echo ""
echo "=== Verify imports in refactored ==="
cd /root/Sales-Tele-Bot_refactored && python3 -c "
import sys; sys.path.insert(0, '.')
from bot.handlers.main_menu import show_main_menu, step_main_menu
print('OK main_menu imports')
from bot.handlers import *
print('OK handlers init imports')
from bot import main
print('OK bot main import')
" 2>&1

echo ""
echo "=== Verify imports in staging ==="
cd /root/staging/bot_src && python3 -c "
import sys; sys.path.insert(0, '.')
from bot.handlers.main_menu import show_main_menu, step_main_menu
print('OK main_menu imports')
from bot.handlers import *
print('OK handlers init imports')
from bot import main
print('OK bot main import')
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
