const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

function runCmd(cmd, timeout = 15000) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, { timeout }, (err, stream) => {
      if (err) return reject(err);
      let out = '', errOut = '';
      stream.on('data', (d) => { out += d.toString(); });
      stream.stderr.on('data', (d) => { errOut += d.toString(); });
      stream.on('close', (code) => resolve({ code, stdout: out.trim(), stderr: errOut.trim() }));
    });
  });
}

async function main() {
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: KEY });
  });
  console.log('=== CONNECTED ===\n');

  // Find any python/node processes running bot tokens
  console.log('--- ANY PROCESS USING BOT TOKENS ---');
  let r = await runCmd('ps aux | grep -E "8545665013|8639289328|main\\.py.*bot|bot.*main\\.py|python.*psvibe|python.*sales" | grep -v grep');
  console.log(r.stdout || '(none)');
  console.log('');

  // Check /proc for processes with BOT_TOKEN in env
  console.log('--- PROCESSES WITH BOT_TOKEN/TOKEN IN ENVIRONMENT ---');
  r = await runCmd(`for pid in $(ps -eo pid --no-headers 2>/dev/null); do tr '\\0' '\\n' < /proc/$pid/environ 2>/dev/null | grep -l "BOT_TOKEN" > /dev/null 2>&1 && echo "PID $pid: $(cat /proc/$pid/cmdline 2>/dev/null | tr '\\0' ' ')" && tr '\\0' '\\n' < /proc/$pid/environ 2>/dev/null | grep "BOT_TOKEN\\|CUSTOMER_BOT_TOKEN"; done`);
  console.log(r.stdout || '(none)');
  console.log('');

  // Check for webhook conflicts  
  console.log('--- TELEGRAM WEBHOOK INFO FOR BOTH BOTS ---');
  r = await runCmd(`curl -s "https://api.telegram.org/bot8545665013:AAFgEuw4V_715Q9yzGOYloinIdbdYXYb8zU/getWebhookInfo" && echo "" && echo "---" && curl -s "https://api.telegram.org/bot8639289328:AAEltJxEgcGbc5D09EHcmMpmCgaaB71vWYs/getWebhookInfo"`);
  console.log(r.stdout);
  console.log('');

  // Check if OpenClaw is running a bot agent that uses these tokens
  console.log('--- OPENCLAW PROCESSES ---');
  r = await runCmd('ps aux | grep -i openclaw | grep -v grep | head -10');
  console.log(r.stdout || '(none)');
  console.log('');

  // Check docker containers
  console.log('--- DOCKER CONTAINERS ---');
  r = await runCmd('docker ps 2>/dev/null || echo "(docker not running or not installed)"');
  console.log(r.stdout);
  console.log('');

  // Critical: Check all Telegram bot polling/webhook processes
  console.log('--- ALL PYTHON PROCESSES ---');
  r = await runCmd('ps aux | grep python | grep -v grep');
  console.log(r.stdout);
  console.log('');

  // Check if the bot's "will resolve automatically" means it calls deleteWebhook or similar
  console.log('--- RECENT JOURNAL FOR BOTH BOTS (last 50 lines each) ---');
  r = await runCmd('journalctl -u psvibe-sale-bot --since "5 min ago" --no-pager 2>/dev/null | tail -30');
  console.log('=== SALES BOT ===');
  console.log(r.stdout);
  console.log('');
  r = await runCmd('journalctl -u psvibe_customer_bot --since "5 min ago" --no-pager 2>/dev/null | tail -30');
  console.log('=== CUSTOMER BOT ===');
  console.log(r.stdout);

  console.log('\n=== AUDIT COMPLETE ===');
  conn.end();
}

main().catch(e => { console.error('ERROR:', e); conn.end(); process.exit(1); });
