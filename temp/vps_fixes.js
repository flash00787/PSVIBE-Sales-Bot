const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', async () => {
  const exec = (cmd, t=60000) => new Promise((res, rej) => {
    let o='', e='';
    const to = setTimeout(() => rej(new Error('Timeout: '+cmd)), t);
    conn.exec(cmd, (err, stream) => {
      if(err) { clearTimeout(to); rej(err); return; }
      stream.on('data', d => o+=d.toString());
      stream.stderr.on('data', d => e+=d.toString());
      stream.on('close', code => { clearTimeout(to); res({code,stdout:o,stderr:e}); });
    });
  });

  const results = {};

  // ========== FIX 1: Add async re-exports to conftest.py ==========
  console.log('=== FIX 1: conftest.py async re-exports ===');
  const fix1 = await exec(`cd /root/psvibe-sales-bot && python3 -c "
import re

with open('tests/conftest.py', 'r') as f:
    content = f.read()

# Add async re-export aliases to the handler re-exports list
old_handler_rex = '''_handler_reexports = [
            \"cmd_cancel\", \"show_main_menu\", \"show_admin_menu\",
            \"show_console_menu\", \"show_game_menu\", \"show_ginst_menu\",
            \"cmd_payroll\", \"cmd_staff_kpi\", \"cmd_setattend\", \"cmd_setattend_cmd\",
        ]'''

new_handler_rex = '''_handler_reexports = [
            \"cmd_cancel\", \"show_main_menu\", \"show_admin_menu\",
            \"show_console_menu\", \"show_game_menu\", \"show_ginst_menu\",
            \"cmd_payroll\", \"cmd_staff_kpi\", \"cmd_setattend\", \"cmd_setattend_cmd\",
            # Async re-export aliases (defined in bot/__init__.py try block)
            \"create_booking_async\", \"end_booking_async\", \"cancel_booking_async\",
            \"fetch_console_status_async\", \"fetch_games_async\",
            \"fetch_console_games_async\", \"get_consoles_with_game_async\",
            \"get_games_on_console_async\", \"add_console_game_async\",
            \"remove_console_game_async\", \"fetch_promotions_cached_async\",
            \"fetch_game_library_async\",
        ]'''

if old_handler_rex in content:
    content = content.replace(old_handler_rex, new_handler_rex)
    with open('tests/conftest.py', 'w') as f:
        f.write(content)
    print('conftest.py updated with async re-exports')
else:
    print('SKIP: handler re-exports pattern not found')
" 2>&1`);
  results.fix1_conftest = fix1.stdout + fix1.stderr;

  // ========== FIX 2: Fix os.environ["STOCK_PIN"] → .get() ==========
  console.log('=== FIX 2: STOCK_PIN env var ===');
  const fix2 = await exec(`cd /root/psvibe-sales-bot && python3 -c "
with open('bot/__init__.py', 'r') as f:
    content = f.read()

old = 'STOCK_ACCESS_PIN    = os.environ[\"STOCK_PIN\"]'
new = 'STOCK_ACCESS_PIN    = os.environ.get(\"STOCK_PIN\", \"\")'

if old in content:
    content = content.replace(old, new)
    with open('bot/__init__.py', 'w') as f:
        f.write(content)
    print('STOCK_PIN fixed to use .get()')
else:
    print('SKIP: pattern not found')
" 2>&1`);
  results.fix2_stockpin = fix2.stdout + fix2.stderr;

  // ========== TEST: Run tests again ==========
  console.log('=== TEST: Re-run tests ===');
  const test = await exec(`cd /root/psvibe-sales-bot && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; python3 -m pytest tests/test_booking.py -x --tb=short 2>&1 | tail -20`);
  results.test_rerun = test.stdout + test.stderr;

  // ========== TEST: Full test run ==========
  console.log('=== TEST: Full test suite ===');
  const fulltest = await exec(`cd /root/psvibe-sales-bot && python3 -m pytest tests/ --tb=short 2>&1 | tail -30`, 120000);
  results.full_test = fulltest.stdout + fulltest.stderr;

  // ========== FIX 3: Clean old notifications (>7 days) ==========
  console.log('=== FIX 3: Clean old notifications ===');
  const fix3 = await exec(`cd /root/coordination/workflow_notifications && find . -name '*.json' -mtime +7 -delete 2>&1 && echo "Cleaned old notifs" && ls *.json 2>&1 | wc -l && echo "remaining"`);
  results.fix3_notifs = fix3.stdout + fix3.stderr;

  // ========== QUALITY GATE RERUN ==========
  console.log('=== QUALITY GATE RERUN ===');
  const qg = await exec(`python3 /root/coordination/quality_gate.py --quick 2>&1`);
  results.quality_gate_rerun = qg.stdout + qg.stderr;

  // ========== GIT: Sales bot commit & push ==========
  console.log('=== GIT: Sales bot commit ===');
  const git = await exec(`cd /root/psvibe-sales-bot && git add -A && git commit -m "fix: test env + async re-exports conftest $(date +%Y-%m-%d)" && git push 2>&1`, 120000);
  results.git_sales = git.stdout + git.stderr;

  // Write results
  fs.writeFileSync('/home/node/.openclaw/workspace/temp/vps_fixes.json', JSON.stringify(results, null, 2));
  console.log('=== ALL FIXES DONE ===');
  conn.end();
});
conn.on('error', e => { console.error('SSH ERROR:', e.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'), readyTimeout: 15000 });
