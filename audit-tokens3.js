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

  // Check psvibe-sales-bot .env (active)
  console.log('--- /root/psvibe-sales-bot/.env ---');
  let r = await runCmd('cat /root/psvibe-sales-bot/.env 2>/dev/null');
  console.log(r.stdout || '(empty or not found)');
  console.log('');

  // Check secrets.env
  console.log('--- /etc/psvibe/secrets.env ---');
  r = await runCmd('cat /etc/psvibe/secrets.env 2>/dev/null | grep -E "BOT_TOKEN|TOKEN"');
  console.log(r.stdout || '(no token entries or file not found)');
  console.log('');

  // Check running services for Environment tokens
  console.log('--- SYSTEMD SERVICE ENV TOKEN CHECKS ---');
  r = await runCmd('for svc in psvibe-sale-bot psvibe_customer_bot psvibe-api psvibe_api; do echo "=== $svc ==="; systemctl show $svc 2>/dev/null | grep -E "Environment(File)?s?" | head -5; echo ""; done');
  console.log(r.stdout);
  console.log('');

  // Check what bot tokens are in /root/.env (active for potential conflicts)
  console.log('--- /root/.env (global export) ---');
  r = await runCmd('cat /root/.env 2>/dev/null');
  console.log(r.stdout || '(empty or not found)');
  console.log('');

  // OpenClaw .env files
  console.log('--- /root/openclaw/.env ---');
  r = await runCmd('grep -E "BOT_TOKEN|TOKEN|TELEGRAM" /root/openclaw/.env 2>/dev/null');
  console.log(r.stdout || '(none)');
  console.log('');

  console.log('--- /root/.openclaw/.env ---');
  r = await runCmd('grep -E "BOT_TOKEN|TOKEN|TELEGRAM" /root/.openclaw/.env 2>/dev/null');
  console.log(r.stdout || '(none)');
  console.log('');

  console.log('--- /opt/openclaw/coco/.env ---');
  r = await runCmd('grep -E "BOT_TOKEN|TOKEN|TELEGRAM" /opt/openclaw/coco/.env 2>/dev/null');
  console.log(r.stdout || '(none)');
  console.log('');

  console.log('--- /opt/openclaw/coco/workspace/vbot/.env ---');
  r = await runCmd('grep -E "BOT_TOKEN|TOKEN|TELEGRAM" /opt/openclaw/coco/workspace/vbot/.env 2>/dev/null');
  console.log(r.stdout || '(none)');
  console.log('');

  // Check /root/api-server/.env
  console.log('--- /root/api-server/.env ---');
  r = await runCmd('cat /root/api-server/.env 2>/dev/null | grep -E "BOT_TOKEN|TOKEN|TELEGRAM"');
  console.log(r.stdout || '(none)');
  console.log('');

  // Look for any /root/openclaw/.env token entries  
  console.log('--- /root/openclaw/.env (full, token-related) ---');
  r = await runCmd('grep -i "bot\\|token" /root/openclaw/.env 2>/dev/null | head -20');
  console.log(r.stdout || '(none)');

  console.log('\n=== AUDIT COMPLETE ===');
  conn.end();
}

main().catch(e => { console.error('ERROR:', e); conn.end(); process.exit(1); });
