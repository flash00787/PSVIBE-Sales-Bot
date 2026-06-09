const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  // FIX 1: Copy fixed main_menu.py from refactored to staging
  // FIX 2: Copy keep_alive.py from Personal-Wallet to both locations
  // FIX 3: Fix __init__.py orphan imports
  // FIX 4: Clean duplicate directories
  // FIX 5: Remove duplicate top-level app.py files
  const cmds = `
echo "=== FIX 1: Copy fixed main_menu.py to staging ==="
cp /root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py /root/staging/bot_src/bot/handlers/main_menu.py
echo "Done. Checking result:"
head -3 /root/staging/bot_src/bot/handlers/main_menu.py

echo ""
echo "=== FIX 2: Copy keep_alive.py ==="
cp /root/Personal-Wallet-Tele-Bot/bot/keep_alive.py /root/Sales-Tele-Bot_refactored/keep_alive.py
cp /root/Personal-Wallet-Tele-Bot/bot/keep_alive.py /root/staging/bot_src/keep_alive.py
echo "Done. Checking:"
ls -la /root/Sales-Tele-Bot_refactored/keep_alive.py /root/staging/bot_src/keep_alive.py

echo ""
echo "=== FIX 3: Fix __init__.py orphan imports (lines 1-6) ==="
python3 -c "
path = '/root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py'
with open(path) as f: lines = f.readlines()
print(f'Before: {len(lines)} lines, first 10:')
for l in lines[:10]: print(repr(l))
# Remove lines 1-6 (orphan imports)
new_lines = lines[6:]
with open(path, 'w') as f: f.writelines(new_lines)
print(f'After: {len(new_lines)} lines, first 10:')
for l in new_lines[:10]: print(repr(l))
"

echo ""
echo "=== FIX 4: Clean duplicate directories ==="
echo "--- Removing /root/Sales-Tele-Bot_refactored/bot/bot/ ---"
rm -rf /root/Sales-Tele-Bot_refactored/bot/bot/
echo "--- Removing /root/staging/bot_src/bot/bot/ ---"
rm -rf /root/staging/bot_src/bot/bot/
echo "--- Removing /root/staging/bot_src/handlers/ ---"
rm -rf /root/staging/bot_src/handlers/
echo "Done. Verifying:"
ls -d /root/Sales-Tele-Bot_refactored/bot/bot/ 2>&1 || echo "  refactored bot/bot/ GONE ✓"
ls -d /root/staging/bot_src/bot/bot/ 2>&1 || echo "  staging bot/bot/ GONE ✓"
ls -d /root/staging/bot_src/handlers/ 2>&1 || echo "  staging handlers/ GONE ✓"

echo ""
echo "=== FIX 5: Remove duplicate top-level app.py ==="
rm -f /root/Sales-Tele-Bot_refactored/app.py
rm -f /root/staging/bot_src/app.py
echo "Done. Verifying:"
ls -la /root/Sales-Tele-Bot_refactored/app.py 2>&1 || echo "  refactored app.py GONE ✓"
ls -la /root/staging/bot_src/app.py 2>&1 || echo "  staging app.py GONE ✓"
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
