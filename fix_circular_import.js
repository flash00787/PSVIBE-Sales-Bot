const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const LOG_FILE = '/tmp/fix_circular_import.txt';

function log(msg) {
  const ts = new Date().toISOString();
  const line = `[${ts}] ${msg}`;
  console.log(line);
  fs.appendFileSync(LOG_FILE, line + '\n');
}

function sshExec(conn, cmd) {
  return new Promise((resolve, reject) => {
    log(`EXEC: ${cmd}`);
    conn.exec(cmd, { pty: true }, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', d => { stdout += d.toString(); });
      stream.stderr.on('data', d => { stderr += d.toString(); });
      stream.on('close', (code, signal) => {
        const out = (stdout + stderr).trim();
        log(`EXIT: ${code} | ${out.substring(0, 500)}`);
        resolve({ code, stdout, stderr, combined: out });
      });
    });
  });
}

async function main() {
  const conn = new Client();
  
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({
      host: '5.223.81.16',
      port: 22,
      username: 'root',
      privateKey: fs.readFileSync(path.resolve('/home/node/.openclaw/workspace/.ssh/id_rsa')),
      readyTimeout: 15000,
    });
  });

  log('SSH connected');

  try {
    // === STEP 1: Check current state ===
    log('=== STEP 1: Current State ===');
    
    let r = await sshExec(conn, 'cd /root/psvibe-sales-bot && tail -35 bot/__init__.py');
    log(`__init__.py tail:\n${r.combined}`);
    
    r = await sshExec(conn, 'cd /root/psvibe-sales-bot && head -20 bot/constants.py');
    log(`constants.py head:\n${r.combined}`);
    
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n '^from\\|^import' bot/__init__.py | head -30`);
    log(`__init__.py imports:\n${r.combined}`);
    
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n '^from\\|^import' bot/constants.py | head -20`);
    log(`constants.py imports:\n${r.combined}`);
    
    // Get more context around line 132 in __init__.py
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && sed -n '125,140p' bot/__init__.py`);
    log(`__init__.py lines 125-140:\n${r.combined}`);

    // === STEP 2: Create fix script ===
    log('=== STEP 2: Apply Fix ===');
    
    // Read the relevant section of __init__.py to find the exact line
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n 'from bot.constants import' bot/__init__.py`);
    log(`constants import lines in __init__.py:\n${r.combined}`);
    
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n 'from bot import' bot/constants.py`);
    log(`from bot import lines in constants.py:\n${r.combined}`);

    // Get full constants.py to understand what it imports from bot
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && cat bot/constants.py`);
    log(`constants.py full:\n${r.combined}`);

    // Get __init__.py around the problematic line
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && wc -l bot/__init__.py`);
    log(`__init__.py line count: ${r.combined}`);

    // Let's see the full structure
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n 'from bot' bot/__init__.py`);
    log(`from bot imports in __init__.py:\n${r.combined}`);

    // ==============================
    // APPLY THE FIX
    // ==============================
    
    // Fix 1: Remove or comment out the circular import in __init__.py
    // Check what's exactly on those lines
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && sed -n '130,140p' bot/__init__.py`);
    log(`__init__.py lines 130-140 exact:\n${r.combined}`);
    
    // Fix approach: In __init__.py, comment out `from bot.constants import *` and 
    // instead, make constants accessible lazily. But first, fix constants.py to not import from bot.
    
    // constants.py imports from bot. We need to check what constants.py needs from bot.
    // Let's get the specific import line
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n 'from bot import' bot/constants.py`);
    log(`constants.py from bot import:\n${r.combined}`);
    
    // Use sed to apply the fix on the VPS
    // Fix: Remove the circular import line from __init__.py
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && sed -i 's/^from bot\\.constants import \\*/# Circular import removed: from bot.constants import */' bot/__init__.py`);
    
    // Now check what constants.py imports from bot and fix that
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n 'from bot import' bot/constants.py`);
    log(`After checking constants.py from bot import:\n${r.combined}`);

    // Let's see the full constants.py to understand what's happening
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && cat -n bot/constants.py`);
    log(`Full constants.py:\n${r.combined}`);

    // Check if the sed command worked on __init__.py
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n 'from bot.constants' bot/__init__.py`);
    log(`After fix - constants import in __init__.py:\n${r.combined}`);

    // ==============================
    // STEP 3: Verify
    // ==============================
    log('=== STEP 3: Verify Import ===');
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -c "import bot.handlers.sales; print('IMPORT OK')" 2>&1`);
    log(`Single import test:\n${r.combined}`);

    // Step 3b: All imports
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -c "
from bot.handlers import sales, booking, admin, members, stock, stock_in, finance, salary_adv
from bot import constants
print('All imports OK')
" 2>&1`);
    log(`All imports test:\n${r.combined}`);

    // ==============================
    // STEP 4: Run Tests
    // ==============================
    log('=== STEP 4: Run Tests ===');
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -m pytest tests/ -q 2>&1 | tail -10`);
    log(`Tests:\n${r.combined}`);

    // ==============================
    // STEP 5: Restart Services
    // ==============================
    log('=== STEP 5: Restart Services ===');
    r = await sshExec(conn, `systemctl restart psvibe-sale-bot.service 2>&1`);
    log(`Restart:\n${r.combined}`);
    
    r = await sshExec(conn, `systemctl status psvibe-sale-bot.service --no-pager -l 2>&1 | head -8`);
    log(`Status:\n${r.combined}`);

    // Wait and check logs
    await new Promise(r => setTimeout(r, 4000));
    
    r = await sshExec(conn, `journalctl -u psvibe-sale-bot.service --no-pager -n 10 --since "30 sec ago" 2>&1`);
    log(`Journal:\n${r.combined}`);

    // ==============================
    // STEP 6: Commit and Push
    // ==============================
    log('=== STEP 6: Commit and Push ===');
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && git add -A && git commit -m "Fix: circular import between __init__.py and constants.py" && git push 2>&1`);
    log(`Git:\n${r.combined}`);

    log('=== ALL DONE ===');

  } finally {
    conn.end();
  }
}

main().catch(err => {
  log(`FATAL: ${err.message}`);
  console.error(err);
  process.exit(1);
});
