const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

function runCmd(cmd, label) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', (data) => { stdout += data.toString(); });
      stream.stderr.on('data', (data) => { stderr += data.toString(); });
      stream.on('close', (code) => {
        resolve({ label, stdout, stderr, code });
      });
    });
  });
}

conn.on('ready', async () => {
  console.log('=== SSH CONNECTED FOR DEEP ANALYSIS ===\n');

  // 1. What is the V1 `bot` module? Check its __init__.py / bot.py
  console.log('=== DEEP 1: V1 bot module structure ===');
  let r = await runCmd('find /root/psvibe-sale-bot/bot/ -type f -name "*.py" 2>/dev/null | head -20', 'bot_files');
  console.log('bot/ Python files:');
  console.log(r.stdout || 'No bot/ directory');

  r = await runCmd('cat /root/psvibe-sale-bot/bot/__init__.py 2>/dev/null | head -60', 'bot_init');
  console.log('bot/__init__.py:');
  console.log(r.stdout || 'NOT FOUND');

  // 2. Check for MMT, now_mmt, today_str definitions
  console.log('\n=== DEEP 2: MMT/now_mmt/today_str definitions in V1 ===');
  r = await runCmd("grep -rn 'def now_mmt\\|def today_str\\|MMT\\|class MMT' /root/psvibe-sale-bot/bot/ 2>/dev/null", 'mmt_defs');
  console.log(r.stdout || 'Not found');

  r = await runCmd("grep -rn 'MMT\\|now_mmt\\|today_str' /root/psvibe-sale-bot/ --include='*.py' 2>/dev/null | grep -v __pycache__ | grep -v '.bak'", 'mmt_all');
  console.log('All MMT/now_mmt/today_str refs:');
  console.log(r.stdout);

  // 3. Check the prompts.py context around the V1 import
  console.log('\n=== DEEP 3: prompts.py context ===');
  r = await runCmd('head -80 /root/psvibe-sale-bot/customer_bot/data/prompts.py', 'prompts_head');
  console.log(r.stdout);

  // 4. Full api.py (the customer_bot's own API layer)
  console.log('\n=== DEEP 4: customer_bot/api.py full ===');
  r = await runCmd('cat /root/psvibe-sale-bot/customer_bot/api.py', 'api_full');
  console.log(r.stdout);

  // 5. Check handlers.py for any V1 imports or refs
  console.log('\n=== DEEP 5: handlers.py V1 refs ===');
  r = await runCmd("grep -n 'from bot\\|from \\.\\.\\|import bot\\|/root/' /root/psvibe-sale-bot/customer_bot/handlers.py 2>/dev/null", 'handler_v1');
  console.log(r.stdout || 'No V1 refs in handlers.py');

  // 6. Check the parent directory structure (what else lives there?)
  console.log('\n=== DEEP 6: Parent directory listing ===');
  r = await runCmd('ls -la /root/psvibe-sale-bot/', 'parent_ls');
  console.log(r.stdout);

  r = await runCmd('ls -la /root/psvibe-sale-bot/bot/ 2>/dev/null | head -30', 'bot_ls');
  console.log('bot/ contents:');
  console.log(r.stdout || 'No bot/ dir');

  // 7. Check if there's a _v1_compat.py or backup
  console.log('\n=== DEEP 7: _v1_compat.py search ===');
  r = await runCmd("find /root/psvibe-sale-bot/ -name '*v1*' -o -name '*compat*' -o -name '*_v1*' 2>/dev/null", 'compat_files');
  console.log('v1/compat files:');
  console.log(r.stdout || 'None found');

  // 8. Check systemd service dependency chain
  console.log('\n=== DEEP 8: psvibe-api.service ===');
  r = await runCmd('systemctl cat psvibe-api 2>/dev/null || cat /etc/systemd/system/psvibe-api.service 2>/dev/null', 'api_service');
  console.log(r.stdout || 'NOT FOUND');

  // 9. What does the V1 api.py or main.py look like?
  console.log('\n=== DEEP 9: V1 main.py or api ===');
  r = await runCmd('ls /root/psvibe-sale-bot/*.py 2>/dev/null', 'root_py');
  console.log('Root .py files:');
  console.log(r.stdout || 'None');
  
  r = await runCmd('ls /root/psvibe-sale-bot/bot/*.py 2>/dev/null', 'bot_py');
  console.log('bot/*.py files:');
  console.log(r.stdout || 'None');

  // 10. Check the secrets.env
  console.log('\n=== DEEP 10: secrets.env ===');
  r = await runCmd('cat /etc/psvibe/secrets.env 2>/dev/null | head -20', 'secrets');
  console.log(r.stdout || 'NOT FOUND');

  // 11. Check the psvibe-api to understand what the customer bot depends on
  console.log('\n=== DEEP 11: psvibe-api process ===');
  r = await runCmd('ps aux | grep -i "uvicorn\\|fastapi\\|gunicorn\\|api" | grep -v grep', 'api_proc');
  console.log(r.stdout);

  // 12. Check API v2 or any V2 API structure
  console.log('\n=== DEEP 12: V2 API check ===');
  r = await runCmd('ls -la /root/psvibe-sale-bot/api/ 2>/dev/null || echo "No api/ dir"; ls -la /root/psvibe-v2/ 2>/dev/null || echo "No psvibe-v2/ dir"', 'v2_check');
  console.log(r.stdout);

  // 13. Check the v1 bot module file(s) for what MMT/now_mmt/today_str do
  console.log('\n=== DEEP 13: bot.py module ===');
  r = await runCmd('cat /root/psvibe-sale-bot/bot.py 2>/dev/null || cat /root/psvibe-sale-bot/bot/bot.py 2>/dev/null', 'bot_module');
  if (!r.stdout.trim()) {
    r = await runCmd("find /root/psvibe-sale-bot/ -maxdepth 2 -name 'bot.py' -o -name 'bot' -type d 2>/dev/null", 'bot_search');
    console.log('Searching for bot module:', r.stdout);
    r = await runCmd("python3 -c \"import sys; sys.path.insert(0,'/root/psvibe-sale-bot'); import bot; print(bot.__file__); print(dir(bot))\" 2>/dev/null", 'import_bot');
    console.log('Python import bot:', r.stdout);
  } else {
    console.log(r.stdout);
  }

  // 14. Check what V1 things the customer_bot/api.py actually calls
  console.log('\n=== DEEP 14: customer_bot api.py dependency on external API ===');
  r = await runCmd("grep -n 'API_BASE_URL\\|localhost\\|_api_get\\|_api_post\\|log_to_sheet' /root/psvibe-sale-bot/customer_bot/api.py 2>/dev/null", 'api_deps');
  console.log(r.stdout);

  conn.end();
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err);
  process.exit(1);
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
