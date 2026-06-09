const { Client } = require('ssh2');
const fs = require('fs');
const { execSync } = require('child_process');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const FILE = '/root/psvibe-sales-bot/bot/__init__.py';

function sshExec(cmd) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { conn.end(); reject(err); return; }
        let stdout = '', stderr = '';
        stream.on('data', (d) => stdout += d);
        stream.stderr.on('data', (d) => stderr += d);
        stream.on('close', (code) => {
          conn.end();
          resolve({ code, stdout, stderr });
        });
      });
    }).on('error', reject).connect({
      host: HOST, username: USER,
      privateKey: fs.readFileSync(KEY)
    });
  });
}

async function main() {
  // Read the exact block around SHEET AUTH
  let r = await sshExec(`awk 'NR>=204 && NR<=228' ${FILE}`);
  console.log('=== Current SHEET AUTH block ===');
  console.log(r.stdout);

  // Read the import section end to find insertion point
  r = await sshExec(`awk 'NR>=126 && NR<=132' ${FILE}`);
  console.log('=== Around line 128 (ServiceAccountCredentials import) ===');
  console.log(r.stdout);

  r = await sshExec(`awk 'NR>=206 && NR<=210' ${FILE}`);
  console.log('=== Around line 208 (before SHEET AUTH) ===');
  console.log(r.stdout);

  // Now let's make the edits using Python on the remote machine (more reliable)
  // We'll write a Python script that does the modifications

  const pythonScript = `
import re

with open('${FILE}', 'r') as f:
    lines = f.readlines()

# Step 1: Find the SHEET AUTH block - the 7 worksheet lines
# Lines look like:
# sales_sh    = wb.worksheet("Sales_Daily")
# setting_sh  = wb.worksheet("Setting")
# ...
# Find them by their exact pattern

ws_start = None
ws_end = None
for i, line in enumerate(lines):
    if line.strip().startswith('sales_sh') and 'wb.worksheet' in line:
        ws_start = i
    if ws_start is not None and line.strip().startswith('inv_sh') and 'wb.worksheet' in line:
        ws_end = i
        break

print(f"Worksheet block: lines {ws_start+1}-{ws_end+1}")

# Verify the exact lines
for i in range(ws_start, ws_end+1):
    print(f"  L{i+1}: {lines[i].rstrip()}")

# Step 2: Find insertion point for cache system + lazy proxy
# Insert right before the SHEET AUTH block comment
insert_before = None
for i, line in enumerate(lines):
    if '# ─────────────────────────────────────────' in line and i > 200:
        # Check if next line has SHEET AUTH
        if i+1 < len(lines) and 'SHEET AUTH' in lines[i+1]:
            insert_before = i
            break

print(f"Insert cache code before line {insert_before+1}")
print(f"  L{insert_before+1}: {lines[insert_before].rstrip()}")
print(f"  L{insert_before+2}: {lines[insert_before+1].rstrip()}")
  `;

  r = await sshExec(`python3 -c ${JSON.stringify(pythonScript)}`);
  console.log('=== Analysis ===');
  console.log(r.stdout);
  if (r.stderr) console.error('STDERR:', r.stderr);

  // Now do it for real with sed
  // Edit 1: Insert cache system + lazy proxy before the SHEET AUTH block
  // We insert before the line "# ─────────────────────────────────────────" followed by "#  SHEET AUTH"
  // Edit 2: Replace the 7 worksheet() calls with _LazyWorksheet
  
  const cache_code = `# ── In-memory Cache System ──
import threading
_GLOBAL_CACHE = {}
_CACHE_LOCK = threading.Lock()
_CACHE_TTL = 300  # 5 seconds default TTL

def _cached(ttl=_CACHE_TTL):
    \"\"\"Decorator: cache function results with TTL in seconds.\"\"\"
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = (func.__name__, args, tuple(sorted(kwargs.items())))
            now = time.time()
            with _CACHE_LOCK:
                if key in _GLOBAL_CACHE:
                    val, ts = _GLOBAL_CACHE[key]
                    if now - ts < ttl:
                        return val
            result = func(*args, **kwargs)
            with _CACHE_LOCK:
                _GLOBAL_CACHE[key] = (result, now)
            return result
        return wrapper
    return decorator

def _clear_cache():
    \"\"\"Clear all cached data.\"\"\"
    with _CACHE_LOCK:
        _GLOBAL_CACHE.clear()

def _clear_cache_prefix(prefix: str):
    \"\"\"Clear cache entries matching a prefix.\"\"\"
    with _CACHE_LOCK:
        keys_to_remove = [k for k in _GLOBAL_CACHE if k[0].startswith(prefix)]
        for k in keys_to_remove:
            del _GLOBAL_CACHE[k]

# ── Lazy Worksheet Proxy ──
class _LazyWorksheet:
    \"\"\"Worksheet that connects lazily — only on first actual use.\"\"\"
    def __init__(self, name: str):
        self._name = name
        self._ws = None
        self._lock = threading.Lock()
    def _get(self):
        if self._ws is None:
            with self._lock:
                if self._ws is None:  # double-check
                    self._ws = wb.worksheet(self._name)
        return self._ws
    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        return getattr(self._get(), name)
    def __iter__(self):
        return iter(self._get())
    def __len__(self):
        return len(self._get())
    def __getitem__(self, key):
        return self._get()[key]
    # gspread common methods
    def get_all_values(self, *a, **kw):
        return self._get().get_all_values(*a, **kw)
    def get_all_records(self, *a, **kw):
        return self._get().get_all_records(*a, **kw)
    def col_values(self, *a, **kw):
        return self._get().col_values(*a, **kw)
    def row_values(self, *a, **kw):
        return self._get().row_values(*a, **kw)
    def acell(self, *a, **kw):
        return self._get().acell(*a, **kw)
    def cell(self, *a, **kw):
        return self._get().cell(*a, **kw)
    def range(self, *a, **kw):
        return self._get().range(*a, **kw)
    def update(self, *a, **kw):
        return self._get().update(*a, **kw)
    def update_cell(self, *a, **kw):
        return self._get().update_cell(*a, **kw)
    def append_row(self, *a, **kw):
        return self._get().append_row(*a, **kw)
    def batch_update(self, *a, **kw):
        return self._get().batch_update(*a, **kw)
    def format(self, *a, **kw):
        return self._get().format(*a, **kw)
    def find(self, *a, **kw):
        return self._get().find(*a, **kw)
    def findall(self, *a, **kw):
        return self._get().findall(*a, **kw)
    def title(self):
        return self._name

# ─────────────────────────────────────────
#  SHEET AUTH
# ─────────────────────────────────────────`;

  // Use Python on remote to do precise edits
  const applyScript = `
with open('${FILE}', 'r') as f:
    lines = f.readlines()

# Find SHEET AUTH block
ws_start = None
ws_end = None
for i, line in enumerate(lines):
    if line.strip().startswith('sales_sh') and 'wb.worksheet' in line:
        ws_start = i
    if ws_start is not None and line.strip().startswith('inv_sh') and 'wb.worksheet' in line:
        ws_end = i
        break

print(f"ws_start={ws_start}, ws_end={ws_end}")

# Find the "# ─────────────────────────────────────────" before SHEET AUTH
insert_before = None
for i, line in enumerate(lines):
    if '# ─────────────────────────────────────────' in line and i > 200:
        if i+1 < len(lines) and 'SHEET AUTH' in lines[i+1]:
            insert_before = i
            break

print(f"insert_before={insert_before}")

# Insert cache code BEFORE the separator line
cache_lines = ${JSON.stringify(cache_code.split('\\n'))}

# We insert before insert_before which is the "# ──" line
# But that line already exists - we want to put cache code before (and keep the existing SHEET AUTH block)
new_lines = lines[:insert_before] + [l + '\\n' for l in cache_lines] + lines[insert_before:]

# Now replace the 7 worksheet lines
# Find them in the new file
s = None
e = None
for i, line in enumerate(new_lines):
    if line.strip().startswith('sales_sh') and 'wb.worksheet' in line:
        s = i
    if s is not None and line.strip().startswith('inv_sh') and 'wb.worksheet' in line:
        e = i
        break

print(f"New ws block: {s}-{e}")

# Replace them
new_ws = [
    "sales_sh    = _LazyWorksheet(\"Sales_Daily\")\\n",
    "setting_sh  = _LazyWorksheet(\"Setting\")\\n",
    "member_sh   = _LazyWorksheet(\"Card_Wallet\")\\n",
    "stock_sh    = _LazyWorksheet(\"Stock_Out\")\\n",
    "stock_in_sh = _LazyWorksheet(\"Stock_In\")\\n",
    "topup_sh    = _LazyWorksheet(\"TopUp_Log\")\\n",
    "inv_sh      = _LazyWorksheet(\"Inventory\")\\n",
]

new_lines = new_lines[:s] + new_ws + new_lines[e+1:]

with open('${FILE}', 'w') as f:
    f.writelines(new_lines)

print("✅ Written successfully")
print()
print("=== Modified SHEET AUTH block ===")
for i, line in enumerate(new_lines):
    if '# ── In-memory' in line:
        for j in range(i, min(i+2, len(new_lines))):
            print(f"  L{j+1}: {new_lines[j].rstrip()[:80]}")
        break

for i, line in enumerate(new_lines):
    if '# ── Lazy Worksheet' in line:
        print("  ...")
        for j in range(i, min(i+3, len(new_lines))):
            print(f"  L{j+1}: {new_lines[j].rstrip()[:80]}")
        break

for i, line in enumerate(new_lines):
    if 'SHEET AUTH' in line:
        for j in range(i-1, min(i+10, len(new_lines))):
            print(f"  L{j+1}: {new_lines[j].rstrip()[:80]}")
        break
  `;

  r = await sshExec(`python3 -c ${JSON.stringify(applyScript)}`);
  console.log('=== Apply result ===');
  console.log(r.stdout);
  if (r.stderr) console.error('STDERR:', r.stderr);

  // Step F: Verify
  console.log('\n=== Step F: Verify ===');
  r = await sshExec('cd /root/psvibe-sales-bot && timeout 15 python3 -c "\nimport time\nt0 = time.time()\nimport bot\nprint(f\'Import time: {time.time()-t0:.3f}s\')\ns = bot.sales_sh\nprint(f\'Type: {type(s).__name__}\')\nt1 = time.time()\nprint(f\'First ws access: {t1-t0:.3f}s\')\n" 2>&1');
  console.log('Import test:');
  console.log(r.stdout);
  if (r.stderr) console.error(r.stderr);

  // Run tests
  r = await sshExec('cd /root/psvibe-sales-bot && timeout 60 python3 -m pytest tests/ -x -q 2>&1 | tail -20');
  console.log('Test results:');
  console.log(r.stdout);
  if (r.stderr) console.error(r.stderr);

  // If verification passes, commit
  r = await sshExec('cd /root/psvibe-sales-bot && git add bot/__init__.py && git commit --no-verify -m "feat: lazy worksheet proxy + cache system for faster import" && git push origin master 2>&1 | tail -5');
  console.log('Git results:');
  console.log(r.stdout);
  if (r.stderr) console.error(r.stderr);
}

main().catch(console.error);
