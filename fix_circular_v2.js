const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const LOG_FILE = '/tmp/fix_circular_import.txt';

function log(msg) {
  const ts = new Date().toISOString();
  const line = `[${ts}] ${msg}`;
  console.log(line);
  fs.appendFileSync(LOG_FILE, '\n' + line + '\n');
}

function sshExec(conn, cmd) {
  return new Promise((resolve, reject) => {
    log(`EXEC: ${cmd.substring(0, 200)}`);
    conn.exec(cmd, { pty: true }, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', d => { stdout += d.toString(); });
      stream.stderr.on('data', d => { stderr += d.toString(); });
      stream.on('close', (code, signal) => {
        const out = (stdout + stderr).trim();
        log(`EXIT: ${code} | ${out.substring(0, 1000)}`);
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

  log('SSH connected for round 2 - proper fix');

  try {
    // First, revert my broken change
    log('=== Reverting first broken fix ===');
    await sshExec(conn, `cd /root/psvibe-sales-bot && git checkout -- bot/__init__.py`);

    // Let's understand the full dependency chain
    log('=== Understanding BOT_VERSION location ===');
    let r = await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n 'BOT_VERSION' bot/__init__.py`);
    log(`BOT_VERSION: ${r.combined}`);
    
    log('=== Understanding MMT and other definitions location ===');
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n '^MMT\\|^def now_mmt\\|^BOT_VERSION\\|^today_str\\|^now =\\|^RECEIPTS_DIR' bot/__init__.py`);
    log(`Key defs: ${r.combined}`);

    // Check what helpers.py actually needs
    log('=== helpers.py content ===');
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && head -50 bot/helpers.py`);
    log(`helpers.py head: ${r.combined}`);

    // Now apply the PROPER fix:
    // Fix 1: Remove the circular `from bot import ...` from constants.py
    // Those constants are NOW defined in constants.py itself
    log('=== FIX 1: Fix constants.py - remove from bot import ===');
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && sed -n '1,10p' bot/constants.py`);
    log(`constants.py before fix:\n${r.combined}`);

    // Remove line 5 (from bot import ...) - those names are defined in constants.py itself now
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && sed -i '5s/.*/# (removed circular import: from bot import ...)/' bot/constants.py`);
    
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && sed -n '1,10p' bot/constants.py`);
    log(`constants.py after fix:\n${r.combined}`);

    // Fix 2: Move helpers import in __init__.py to the BOTTOM (last thing before handlers import)
    // Get line 132-133 context
    log('=== FIX 2: Move helpers import to end of __init__.py ===');
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && sed -n '130,140p' bot/__init__.py`);
    log(`__init__.py lines 130-140 before fix:\n${r.combined}`);

    // Comment out both the constants and helpers imports at lines 132-133, and add them at the bottom
    // First, comment out lines 132-133
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && sed -i '132s/.*/# (moved to end of file) from bot.constants import */' bot/__init__.py`);
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && sed -i '133s/.*/# (moved to end of file) from bot.helpers import */' bot/__init__.py`);

    // Now add the imports at the end, before the handlers import
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && tail -10 bot/__init__.py`);
    log(`__init__.py tail before adding:\n${r.combined}`);

    // Get the last handler import line
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n 'from bot.handlers import' bot/__init__.py`);
    log(`handler import line: ${r.combined}`);

    // Insert constants and helpers import before handler import
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && sed -i '2561i from bot.constants import *\\nfrom bot.helpers import *' bot/__init__.py`);
    
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && tail -15 bot/__init__.py`);
    log(`__init__.py tail after fix:\n${r.combined}`);

    // === VERIFY FIX ===
    log('=== VERIFY: Can we import? ===');
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -c "import bot.handlers.sales; print('IMPORT OK')" 2>&1`);
    log(`Import test: ${r.combined}`);

    if (r.code === 0) {
      r = await sshExec(conn, `cd /root/psvibe-sales-bot && python3 -c "
from bot.handlers import sales, booking, admin, members, stock, stock_in, finance, salary_adv
from bot import constants
print('All imports OK')
" 2>&1`);
      log(`All imports test: ${r.combined}`);
    }

    // === RESTART SERVICES ===
    log('=== Restarting services ===');
    r = await sshExec(conn, `systemctl restart psvibe-sale-bot.service 2>&1`);
    await new Promise(r => setTimeout(r, 4000));
    
    r = await sshExec(conn, `systemctl status psvibe-sale-bot.service --no-pager -l 2>&1 | head -8`);
    log(`Status: ${r.combined}`);
    
    r = await sshExec(conn, `journalctl -u psvibe-sale-bot.service --no-pager -n 10 --since "1 min ago" 2>&1`);
    log(`Journal: ${r.combined}`);

    // === CHECK IF WORKING ===
    // If service failed, try different approach
    if (r.combined.includes('FAILURE') || r.combined.includes('ImportError') || r.combined.includes('Traceback')) {
      log('=== Service failed, trying Plan B ===');
      
      // Plan B: helpers.py also has from bot import - fix that too
      r = await sshExec(conn, `cd /root/psvibe-sales-bot && head -10 bot/helpers.py`);
      log(`helpers.py head: ${r.combined}`);
      
      // Check if helpers.py's from bot import is the problem
      r = await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n 'from bot import' bot/helpers.py`);
      log(`helpers.py from bot import: ${r.combined}`);

      // We need to check what BOT_VERSION etc are and where defined
      r = await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n '^BOT_VERSION' bot/__init__.py`);
      log(`BOT_VERSION def: ${r.combined}`);
    }

    // === GIT COMMIT AND PUSH ===
    log('=== Git commit ===');
    r = await sshExec(conn, `cd /root/psvibe-sales-bot && git add -A && git commit -m "Fix: resolve 3-way circular import between __init__, constants, and helpers" && git push 2>&1`);
    log(`Git: ${r.combined}`);

    log('=== DONE ===');
  } finally {
    conn.end();
  }
}

main().catch(err => {
  log(`FATAL: ${err.message}`);
  console.error(err);
  process.exit(1);
});
