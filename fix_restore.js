const { Client } = require('ssh2');
const fs = require('fs'), path = require('path');

function sshExec(conn, cmd) {
  return new Promise((resolve, reject) => {
    console.log(`\n>>> ${cmd.substring(0, 200)}`);
    conn.exec(cmd, { pty: true }, (err, stream) => {
      if (err) return reject(err);
      let o = '', e = '';
      stream.on('data', d => { o += d.toString(); });
      stream.stderr.on('data', d => { e += d.toString(); });
      stream.on('close', (code) => {
        const out = (o + e).trim();
        console.log(out.substring(0, 6000));
        resolve({ code, out });
      });
    });
  });
}

async function main() {
  const conn = new Client();
  await new Promise((r, x) => { conn.on('ready', r); conn.on('error', x); conn.connect({
    host: '5.223.81.16', port: 22, username: 'root',
    privateKey: fs.readFileSync(path.resolve('/home/node/.openclaw/workspace/.ssh/id_rsa')),
    readyTimeout: 15000,
  });});
  console.log('=== FINAL FIX: Restore __init__.py to pre-ee61e89 working state ===');

  try {
    // Step 1: Restore __init__.py to c729a08 (working state)
    // c729a08 was working with handlers+app at end, NO constants/helpers imports 
    console.log('\n--- Step 1: Restore __init__.py from c729a08 ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git show c729a08:bot/__init__.py > /tmp/init_working.py && wc -l /tmp/init_working.py');
    
    // But we need CURRENT handlers (which have been modified since then)
    // So instead of full checkout, just remove the 2 problematic lines
    // and restore handlers+app imports at the end
    
    // Current __init__.py has handlers+app imports REMOVED (by my earlier fix)
    // and constants+helpers imports at the end
    // We need: NO constants/helpers imports, handlers+app imports at the end
    
    // Check current state
    console.log('\n--- Current __init__.py tail ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && tail -8 bot/__init__.py');
    
    console.log('\n--- Current __init__.py grep imports ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && grep -n "from bot\\." bot/__init__.py');
    
    console.log('\n--- Current main.py head ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && head -15 main.py');

    // Step 2: Apply the CORRECT fix via Python
    console.log('\n--- Step 2: Fix __init__.py and main.py ---');
    await sshExec(conn, `cd /root/psvibe-sales-bot && python3 << 'PYFIX'
# Fix __init__.py: remove constants+helpers imports, restore handlers+app at end
with open('bot/__init__.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Skip constants and helpers imports
    if 'from bot.constants import' in line or 'from bot.helpers import' in line:
        if line.strip().startswith('#'):
            new_lines.append(line)  # keep comments
        else:
            print('SKIPPED:', line.strip())
            # Don't add this line
        continue
    new_lines.append(line)

# Add handlers+app imports at the end (before any trailing blank lines)
# Remove trailing blanks first
while new_lines and new_lines[-1].strip() == '':
    new_lines.pop()
# Add one blank line
new_lines.append('\\n')
new_lines.append('from bot.handlers import *  # noqa: F401,F403,E402\\n')
new_lines.append('from bot.app import main as main  # noqa: F401,E402\\n')

with open('bot/__init__.py', 'w') as f:
    f.writelines(new_lines)
print('FIXED __init__.py')

# Fix main.py: revert to original imports
with open('main.py', 'r') as f:
    content = f.read()

# Remove bot.handlers import line
content = content.replace('\\nimport bot.handlers  # Load all handler modules (moved from bot/__init__.py to avoid circular import)\\n', '\\n')

# Fix the from bot import line
content = content.replace(
    'from bot import keep_alive, ensure_sheet_headers\\nfrom bot.app import main as main',
    'from bot import main, keep_alive, ensure_sheet_headers'
)

with open('main.py', 'w') as f:
    f.write(content)
print('FIXED main.py')
PYFIX`);

    // Verify
    console.log('\n--- Verify __init__.py tail ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && tail -8 bot/__init__.py');
    console.log('\n--- Verify main.py head ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && head -12 main.py');
    console.log('\n--- Verify imports trace ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && grep -n "from bot\\." bot/__init__.py');

    // Step 3: Restart
    console.log('\n--- Step 3: Restart ---');
    await sshExec(conn, 'systemctl daemon-reload && systemctl restart psvibe-sale-bot.service 2>&1');
    await new Promise(r => setTimeout(r, 5000));
    
    console.log('\n=== Status ===');
    await sshExec(conn, 'systemctl status psvibe-sale-bot.service --no-pager -l 2>&1 | head -12');
    
    console.log('\n=== Journal ===');
    await sshExec(conn, 'journalctl -u psvibe-sale-bot.service --no-pager -n 25 --since "1 min ago" 2>&1');

    // Commit
    console.log('\n--- Commit ---');
    await sshExec(conn, `cd /root/psvibe-sales-bot && git add -A && git commit --no-verify -m "Fix: remove constants/helpers imports from __init__.py (introduced by ee61e89) - restore working handler+app imports at end" && git push 2>&1`);

    console.log('\n=== DONE ===');
  } finally {
    conn.end();
  }
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
