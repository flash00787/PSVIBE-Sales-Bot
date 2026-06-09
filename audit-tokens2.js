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

  // All env files (excluding known noise paths)
  console.log('--- ALL .env FILES ---');
  const r1 = await runCmd(`find / -name ".env" -type f 2>/dev/null | grep -v "__pycache__\\|node_modules\\|\\.git\\|/proc/\\|/sys/\\|/snap/\\|/var/lib/\\|/usr/lib/\\|/var/log/\\|/venv/\\|\\.venv\\|/tmp/" | sort`);
  const envFiles = r1.stdout.split('\n').filter(l => l.trim());
  envFiles.forEach(f => console.log(f));
  console.log('');

  // Extract BOT_TOKEN, TOKEN, CUSTOMER_BOT_TOKEN from each .env
  console.log('--- TOKEN EXTRACTION FROM ALL .env FILES ---');
  for (const f of envFiles) {
    const r = await runCmd(`grep -E "^(BOT_TOKEN|TOKEN|CUSTOMER_BOT_TOKEN|STAFF_BOT_TOKEN|TELEGRAM_BOT_TOKEN)\\s*=" "${f}" 2>/dev/null`);
    if (r.stdout.trim()) {
      console.log(`\n[${f}]`);
      r.stdout.split('\n').forEach(l => console.log('  ' + l.trim()));
    }
  }
  console.log('');

  // Check BOT_TOKEN in active running .env (psvibe-sales-bot) vs secrets.env
  console.log('--- ACTIVE RUNNING BOTS: Token comparison ---');
  const r2 = await runCmd(`echo "=== /root/psvibe-sales-bot/.env ===" && grep "^BOT_TOKEN\\|^CUSTOMER_BOT_TOKEN" /root/psvibe-sales-bot/.env 2>/dev/null && echo "" && echo "=== /etc/psvibe/secrets.env ===" && grep "^BOT_TOKEN\\|^CUSTOMER_BOT_TOKEN\\|^TELEGRAM_BOT_TOKEN" /etc/psvibe/secrets.env 2>/dev/null && echo "" && echo "=== /root/ACM-Personal-Wallet/.env ===" && grep "^BOT_TOKEN\\|^TOKEN" /root/ACM-Personal-Wallet/.env 2>/dev/null && echo "" && echo "=== /opt/yyo-personal-wallet/.env ===" && grep "^BOT_TOKEN\\|^TOKEN" /opt/yyo-personal-wallet/.env 2>/dev/null && echo "" && echo "=== /opt/construction-bot/.env ===" && grep "^BOT_TOKEN\\|^TOKEN" /opt/construction-bot/.env 2>/dev/null`);
  console.log(r2.stdout);
  console.log('');

  // Also check .env at /root/.env (sometimes there's one)
  console.log('--- /root/.env if exists ---');
  const r3 = await runCmd(`cat /root/.env 2>/dev/null | grep -E "BOT_TOKEN|TOKEN" || echo "(not found)"`);
  console.log(r3.stdout);
  console.log('');

  // Check systemd service EnvironmentFile references
  console.log('--- SYSTEMD SERVICE TOKEN SOURCES ---');
  const r4 = await runCmd(`grep -n "EnvironmentFile\\|BOT_TOKEN\\|TOKEN=" /etc/systemd/system/psvibe*.service /etc/systemd/system/psvibe*/*.service 2>/dev/null`);
  console.log(r4.stdout || '(none)');
  console.log('');

  // Check for running processes using bot tokens
  console.log('--- ACTIVE PROCESSES WITH BOT TOKENS ---');
  const r5 = await runCmd(`ps aux | grep -i "BOT_TOKEN\\|telegram" | grep -v grep`);
  console.log(r5.stdout || '(none)');
  console.log('');

  // Hash comparison for service_account.json files
  console.log('--- SERVICE_ACCOUNT.JSON HASHES (to identify duplicates) ---');
  const r6 = await runCmd(`find /root/ /opt/ -name "service_account.json" -type f 2>/dev/null -exec sh -c 'echo "{} $(md5sum "{}" | cut -d" " -f1)"' \\; | sort`);
  console.log(r6.stdout);
  console.log('');

  console.log('=== AUDIT COMPLETE ===');
  conn.end();
}

main().catch(e => { console.error('ERROR:', e); conn.end(); process.exit(1); });
