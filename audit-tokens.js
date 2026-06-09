const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

function runCmd(cmd, timeout = 15000) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, { timeout }, (err, stream) => {
      if (err) return reject(err);
      let out = '', errOut = '';
      stream.on('data', (d) => { out += d.toString(); });
      stream.stderr.on('data', (d) => { errOut += d.toString(); });
      stream.on('close', (code) => {
        resolve({ code, stdout: out.trim(), stderr: errOut.trim() });
      });
    });
  });
}

async function main() {
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({ host: HOST, port: 22, username: USER, privateKey: KEY });
  });
  console.log('=== CONNECTED ===\n');

  // Step 1: Find all .env files
  console.log('--- STEP 1: All .env files ---');
  const r1 = await runCmd(`find / -name ".env" -type f 2>/dev/null | grep -v "__pycache__\\|node_modules\\|\\.git\\|proc\\|sys\\|snap\\|var/lib\\|usr/lib\\|var/log\\|venv\\|\\.venv\\|/sys/\\|/proc/"`);
  console.log(r1.stdout || '(none found)');
  console.log('');

  // Step 2: Extract BOT_TOKEN from each known env file
  console.log('--- STEP 2: Extract BOT_TOKEN / TOKEN from .env files ---');
  const knownEnvs = [
    '/root/psvibe-sales-bot/.env',
    '/root/ACM-Personal-Wallet/.env',
    '/opt/yyo-personal-wallet/.env',
    '/opt/construction-bot/.env',
  ];
  
  // Also find any other .env files not in known list
  const envFiles = r1.stdout.split('\n').filter(l => l.trim());
  
  for (const envFile of knownEnvs) {
    const r = await runCmd(`cat "${envFile}" 2>/dev/null`);
    if (r.stdout) {
      const lines = r.stdout.split('\n').filter(l => l.match(/BOT_TOKEN|TOKEN/i));
      console.log(`--- ${envFile} ---`);
      lines.forEach(l => console.log(l.trim()));
      console.log('');
    } else {
      console.log(`${envFile}: (not found or empty)`);
    }
  }

  // Check additional .env files not in known list
  for (const envFile of envFiles) {
    if (!knownEnvs.includes(envFile)) {
      const r = await runCmd(`cat "${envFile}" 2>/dev/null`);
      if (r.stdout) {
        const lines = r.stdout.split('\n').filter(l => l.match(/BOT_TOKEN|TOKEN/i));
        if (lines.length > 0) {
          console.log(`--- Additional: ${envFile} ---`);
          lines.forEach(l => console.log(l.trim()));
          console.log('');
        }
      }
    }
  }

  // Step 3: Also look in systemd service files for tokens
  console.log('--- STEP 3: Systemd service Environment / EnvironmentFile ---');
  const r3 = await runCmd(`grep -rn "BOT_TOKEN\\|TOKEN" /etc/systemd/system/ 2>/dev/null | grep -v ".DISABLED"`);
  if (r3.stdout) console.log(r3.stdout);
  else console.log('(none found)');
  console.log('');

  // Step 4: Check for hardcoded tokens
  console.log('--- STEP 4: Hardcoded tokens (8545665013, 8639289328) ---');
  const r4a = await runCmd(`grep -rn "8545665013" /root/ /opt/ 2>/dev/null | grep -v "\\.git\\|__pycache__\\|\\.pyc\\|node_modules\\|\\.log\\|backups\\|\\.DISABLED"`);
  if (r4a.stdout) console.log('8545665013:', r4a.stdout);
  else console.log('8545665013: (none found outside excluded dirs)');
  
  const r4b = await runCmd(`grep -rn "8639289328" /root/ /opt/ 2>/dev/null | grep -v "\\.git\\|__pycache__\\|\\.pyc\\|node_modules\\|\\.log\\|backups\\|\\.DISABLED"`);
  if (r4b.stdout) console.log('8639289328:', r4b.stdout);
  else console.log('8639289328: (none found outside excluded dirs)');
  console.log('');

  // Step 5: Check service_account.json
  console.log('--- STEP 5: service_account.json locations ---');
  const r5 = await runCmd(`find /root/ /opt/ -name "service_account.json" -type f 2>/dev/null`);
  if (r5.stdout) {
    console.log('Files:', r5.stdout);
    // Also get sizes to see if they're duplicates
    console.log('');
    await runCmd(`find /root/ /opt/ -name "service_account.json" -type f -exec ls -la {} \\; 2>/dev/null`).then(r => console.log('Details:', r.stdout));
  } else {
    console.log('(none found)');
  }
  console.log('');

  // Step 6: Check for any TOKEN= in main Python/bot files
  console.log('--- STEP 6: TOKEN= in Python files ---');
  const r6 = await runCmd(`grep -rn "TOKEN\\s*=" /root/psvibe-sales-bot/*.py /opt/construction-bot/*.py /opt/yyo-personal-wallet/*.py /root/ACM-Personal-Wallet/*.py 2>/dev/null | head -20`);
  if (r6.stdout) console.log(r6.stdout);
  else console.log('(none or files not found)');
  console.log('');

  // Step 7: Check config.py or settings files
  console.log('--- STEP 7: Config/settings token references ---');
  const r7 = await runCmd(`grep -rn "token\\|TOKEN" /root/ /opt/ 2>/dev/null | grep -i "config\\|settings" | grep -v "__pycache__\\|\\.pyc\\|node_modules\\|\\.git\\|\\.log\\|venv" | head -20`);
  console.log(r7.stdout || '(none found)');
  
  console.log('\n=== AUDIT COMPLETE ===');
  conn.end();
}

main().catch(e => { console.error('ERROR:', e); conn.end(); process.exit(1); });
