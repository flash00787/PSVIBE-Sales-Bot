const { Client } = require('ssh2');
const fs = require('fs');

const VPS = '5.223.81.16';
const KEY = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const DIR = '/root/Aung Chan Myint/Sales-Tele-Bot';

function ssh(cmd) {
  return new Promise((resolve, reject) => {
    const conn = new Client(); let out = '';
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { conn.end(); reject(err); return; }
        stream.on('data', d => out += d.toString());
        stream.stderr.on('data', d => out += d.toString());
        stream.on('close', () => { conn.end(); resolve(out); });
      });
    }).on('error', e => { conn.end(); reject(e); })
    .connect({ host: VPS, username: 'root',
      privateKey: fs.readFileSync(KEY), readyTimeout: 30000 });
  });
}

(async () => {
  // Write audit script to VPS temp file to avoid quoting hell
  const auditScript = `cd "${DIR}"

echo "=== MAIN.PY SYNTAX ==="
python3 << 'PYEOF'
import ast
try:
    with open("main.py") as f: ast.parse(f.read())
    print("PASS")
except SyntaxError as e:
    print(f"FAIL: {e}")
PYEOF

echo "=== CUSTOMER_BOT SYNTAX ==="
python3 << 'PYEOF'
import ast
try:
    with open("customer_bot.py") as f: ast.parse(f.read())
    print("PASS")
except SyntaxError as e:
    print(f"FAIL: {e}")
PYEOF

echo "=== ALL PY FILES SYNTAX ==="
python3 << 'PYEOF'
import ast, os
errs=[]
for root,dirs,files in os.walk("."):
    if "__pycache__" in root or ".venv" in root: continue
    for f in files:
        if not f.endswith(".py"): continue
        fp = os.path.join(root,f)
        try:
            with open(fp) as h: ast.parse(h.read())
        except SyntaxError as e:
            errs.append(f"{fp}: {e}")
if errs:
    for e in errs: print(e)
else:
    print("ALL PY FILES PASS")
PYEOF

echo "=== TRY/EXCEPT BALANCE CHECK ==="
python3 << 'PYEOF'
with open("main.py") as f:
    lines = f.readlines()
depth = 0
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if stripped.startswith("try:") and (stripped.endswith(":") or stripped == "try:"):
        depth += 1
    if stripped.startswith("except") and stripped.endswith(":"):
        depth -= 1
    if stripped.startswith("finally:") or stripped.startswith("else:"):
        if "try:" in lines[i-2].strip() if i>1 else False:
            pass
print(f"Net try/except balance: {depth} (should be 0)")

# Find the broken block near line 6996
print("\\n=== Lines 6990-7010 ===")
for l in lines[6989:7010]:
    print(f"{lines.index(l)+1}: {l.rstrip()}")
PYEOF

echo "=== FUNCTIONS ==="
echo "main.py:" && grep -c "^def \|^async def " main.py
echo "bot/handlers.py:" && grep -c "^def \|^async def " bot/handlers.py
echo "bot/__init__.py:" && grep -c "^def \|^async def " bot/__init__.py
echo "bot/app.py:" && grep -c "^def \|^async def " bot/app.py
echo "customer_bot.py:" && grep -c "^def \|^async def " customer_bot.py

echo "=== REPLIT APIS ==="
echo "main.py:" && grep -n "def _replit" main.py
echo "bot/__init__.py:" && grep -n "def _replit" bot/__init__.py

echo "=== _replit_patch IN HANDLERS ==="
grep -n "_replit_patch" bot/handlers.py | head -10

echo "=== AUTH MIDDLEWARE ==="
echo "main.py:" && grep -n "TypeHandler\|group=-999\|_auth_middleware" main.py | head -5
echo "bot/app.py:" && grep -n "TypeHandler\|group=-999\|_auth_middleware" bot/app.py | head -5

echo "=== CONVERSATION HANDLER STATES ==="
echo "main.py states:" && grep "step_" main.py | grep "^def " | wc -l
echo "bot/app.py ConversationHandler states:"
grep "BotState\.\|entry_points\|fallbacks" bot/app.py | head -10

echo "=== RUNNING BOT SERVICES ==="
ls -la /etc/systemd/system/psvibe*.service 2>&1
systemctl list-units --type=service --state=running 2>&1 | grep -i vibe
systemctl list-units --type=service --state=running 2>&1 | grep -i ps

echo "=== BOT PROCESSES ==="
ps aux | grep python | grep -v grep | grep -v unattended
`;

  await ssh(`cat > /tmp/audit_vps.sh << 'SCRIPTMARKER'\n${auditScript}\nSCRIPTMARKER\nchmod +x /tmp/audit_vps.sh && bash /tmp/audit_vps.sh`);
  
  let result = await ssh('bash /tmp/audit_vps.sh 2>&1');
  fs.writeFileSync('/home/node/.openclaw/workspace/VPS_AUDIT_RESULT.txt', result);
  console.log(result);
})();
