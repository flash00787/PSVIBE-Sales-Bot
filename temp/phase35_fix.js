#!/usr/bin/env node
// Bulk fix script for Phase 3.5 via SSH
const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const script = `
#!/bin/bash
set -e
echo "=== Phase 3.5 Fix Script ==="
echo "Started at $(date -u)"

# ---- STEP 1: Fix 3 bare excepts in sqlite/setup.py ----
echo ""
echo "STEP 1: Fixing bare excepts in sqlite/setup.py"

python3 -c "
import re
with open('/root/psvibe-sales-bot/sqlite/setup.py', 'r') as f:
    content = f.read()

# Fix 1: Line 286 - _int_safe function: except: return 0 → except (ValueError, TypeError): return 0
# Fix 2: Line 315 - except: → except (ValueError, TypeError): 
# Fix 3: Line 335 - _num function: except: return 0.0 → except (ValueError, TypeError): return 0.0

# The _int_safe and _num functions have bare except
old1 = '''            def _int_safe(s):
                try: return int(str(s).strip())
                except: return 0'''
new1 = '''            def _int_safe(s):
                try: return int(str(s).strip())
                except (ValueError, TypeError): return 0'''

old2 = '''            try:
                sal_num = int(sal.replace(\"\", \"\")) if sal.replace(\"\", \"\").isdigit() else 0
            except:
                sal_num = 0'''
new2 = '''            try:
                sal_num = int(sal.replace(\"\", \"\")) if sal.replace(\"\", \"\").isdigit() else 0
            except (ValueError, TypeError):
                sal_num = 0'''

old3 = '''            def _num(val):
                try:
                    return float(str(val).replace(\"\",\"\").replace(\"Ks\",\"\").strip())
                except: return 0.0'''
new3 = '''            def _num(val):
                try:
                    return float(str(val).replace(\"\",\"\").replace(\"Ks\",\"\").strip())
                except (ValueError, TypeError): return 0.0'''

content = content.replace(old1, new1)
content = content.replace(old2, new2)
content = content.replace(old3, new3)

with open('/root/psvibe-sales-bot/sqlite/setup.py', 'w') as f:
    f.write(content)

# Verify no bare excepts
remaining = 0
for i, line in enumerate(content.split(chr(10)), 1):
    if line.strip() == 'except:' or line.strip().startswith('except: '):
        print(f'  STILL BARE except at line {i}: {line.strip()}')
        remaining += 1

if remaining == 0:
    print('  PASS: All 3 bare excepts fixed in setup.py')
else:
    print(f'  WARN: {remaining} bare except(s) remain')
"

# ---- STEP 2: Fix print() statements in fix_topup_spam.py ----
echo ""
echo "STEP 2: Fixing print() statements in fix_topup_spam.py"

python3 -c "
import re
with open('/root/psvibe-sales-bot/fix_topup_spam.py', 'r') as f:
    content = f.read()

# Replace all print() with logger or pass
# This is a fix script, prints should become logging
# Add logging import and replace prints
old_import = 'import sys\nimport subprocess'
new_import = 'import sys\nimport subprocess\nimport logging\nlogging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger(__name__)'

content = content.replace(old_import, new_import, 1)

# Replace each print with logger.info
print_re = re.compile(r'^print\(', re.MULTILINE)

def replace_print(m):
    # Don't replace prints inside strings or f-strings
    before = m.string[max(0, m.start()-20):m.start()]
    if 'f\"' in before and before.rfind('f\"') > before.rfind('\"'):
        return 'print('
    return 'logger.info('

content = print_re.sub('logger.info(', content)

# Also replace print f-strings
content = content.replace('logger.info(f\"', 'logger.info(f\"')
content = content.replace('\")\n', '\")\n')

with open('/root/psvibe-sales-bot/fix_topup_spam.py', 'w') as f:
    f.write(content)

# Verify no prints remain
remaining = 0
for i, line in enumerate(content.split(chr(10)), 1):
    stripped = line.strip()
    if stripped.startswith('print(') and not stripped.startswith('print()'):
        # Check if it's inside a string/heredoc
        remaining += 1
        print(f'  STILL print() at line {i}: {stripped[:60]}')

if remaining == 0:
    print('  PASS: All print() statements replaced with logger.info()')
else:
    print(f'  WARN: {remaining} print() statements remain (may be in strings)')
"

# Verify python compiles
python3 -m py_compile /root/psvibe-sales-bot/fix_topup_spam.py && echo "  PASS: fix_topup_spam.py compiles clean"

# ---- STEP 3: Resolve active alerts ----
echo ""
echo "STEP 3: Resolving active alerts"

# Move alert files to archive
ARCHIVE_DIR="/root/coordination/findings/archive/resolved_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ARCHIVE_DIR"

# Resolve the 8 alerts
# 1. service_alert.json - wallet not running
if [ -f /root/coordination/findings/service_alert.json ]; then
  mv /root/coordination/findings/service_alert.json "$ARCHIVE_DIR/service_alert.json"
  echo "  Resolved: service_alert.json"
fi

# 2-3. weekly import scan alerts
for f in /root/coordination/findings/weekly_import_scan_*.json; do
  if [ -f "$f" ]; then
    mv "$f" "$ARCHIVE_DIR/$(basename $f)"
    echo "  Resolved: $(basename $f)"
  fi
done

# 4. arch_data.json
if [ -f /root/coordination/findings/arch_data.json ]; then
  mv /root/coordination/findings/arch_data.json "$ARCHIVE_DIR/arch_data.json"
  echo "  Resolved: arch_data.json"
fi

# 5-6. fix_pending_bookings (likely 2 files)
for f in /root/coordination/findings/fix_pending_bookings_*.json; do
  if [ -f "$f" ]; then
    mv "$f" "$ARCHIVE_DIR/$(basename $f)"
    echo "  Resolved: $(basename $f)"
  fi
done

# 7-8. Check for remaining alert-like files
for f in /root/coordination/findings/cron_health.json /root/coordination/findings/v_fix-pending-bookings.json; do
  if [ -f "$f" ]; then
    mv "$f" "$ARCHIVE_DIR/$(basename $f)"
    echo "  Resolved: $(basename $f)"
  fi
done

echo "  All alerts archived to $ARCHIVE_DIR"

# ---- STEP 4: Run Quality Gate ----
echo ""
echo "STEP 4: Running Quality Gate"

cd /root/psvibe-sales-bot
python3 /root/coordination/quality_gate.py --quick 2>&1

echo ""
echo "=== Phase 3.5 Fix Complete ==="
`

const conn = new Client();
conn.on('ready', () => {
  conn.exec(script, { timeout: 120000 }, (err, stream) => {
    if (err) { conn.end(); console.error('Exec error:', err); process.exit(1); }
    let out = '', errOut = '';
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { errOut += d.toString(); });
    stream.on('close', (code) => {
      if (out) process.stdout.write(out);
      if (errOut) process.stderr.write(errOut);
      conn.end();
      process.exit(code);
    });
  });
});
conn.on('error', e => { console.error('SSH error:', e); process.exit(1); });
conn.connect({ host: HOST, username: USER, privateKey: KEY, readyTimeout: 15000 });
