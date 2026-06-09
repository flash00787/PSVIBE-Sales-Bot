const { Client } = require('ssh2');
const { readFileSync } = require('fs');
const path = require('path');
const os = require('os');

const MAIN_HOST = '5.223.81.16';
const MAIN_USER = 'root';
const MAIN_KEY = readFileSync(path.join(__dirname, '.ssh', 'id_rsa'));

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function sshExec(connConfig, command, label) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let stdout = '', stderr = '';
    conn.on('ready', () => {
      console.log(`\n=== [${label}] Connected`);
      conn.exec(command, (err, stream) => {
        if (err) { conn.end(); return reject(err); }
        stream.on('data', d => { stdout += d.toString(); });
        stream.stderr.on('data', d => { stderr += d.toString(); });
        stream.on('close', (code) => {
          conn.end();
          if (code === 0) {
            console.log(`[${label}] OK (exit ${code})`);
          } else {
            console.log(`[${label}] Exit ${code}`);
          }
          resolve({ stdout, stderr, code });
        });
      });
    });
    conn.on('error', e => { conn.end(); reject(e); });
    conn.connect(connConfig);
    // Set a reasonable timeout
    setTimeout(() => {
      try { conn.end(); } catch(e) {}
    }, 30000);
  });
}

function sftpPut(connConfig, localPath, remotePath, label) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      console.log(`\n=== [${label}] SFTP PUT: ${localPath} -> ${remotePath}`);
      conn.sftp((err, sftp) => {
        if (err) { conn.end(); return reject(err); }
        const rs = require('fs').createReadStream(localPath);
        const ws = sftp.createWriteStream(remotePath);
        let bytes = 0;
        rs.on('data', d => { bytes += d.length; if (bytes % (5*1024*1024) < 65536) process.stdout.write('.'); });
        rs.on('end', () => {
          console.log(`\n[${label}] Uploaded ${(bytes/1024/1024).toFixed(1)} MB`);
          conn.end();
          resolve(bytes);
        });
        rs.on('error', e => { conn.end(); reject(e); });
        rs.pipe(ws);
        setTimeout(() => { try { conn.end(); } catch(e) {} }, 60000);
      });
    });
    conn.on('error', e => { conn.end(); reject(e); });
    conn.connect(connConfig);
  });
}

async function sshExecSafe(config, cmd, label) {
  try {
    return await sshExec(config, cmd, label);
  } catch (e) {
    console.log(`[${label}] Connection error: ${e.message}, retrying after 3s...`);
    await sleep(3000);
    return await sshExec(config, cmd, label + '-retry');
  }
}

async function main() {
  console.log('🚀 Migration Continuation - Extract & Setup');
  console.log('============================================\n');
  const mcfg = { host: MAIN_HOST, port: 22, username: MAIN_USER, privateKey: MAIN_KEY };

  // ============ STEP 5: Extract & Rename ============
  console.log('\n📦 STEP 5: Verify archive & extract on Main VPS');
  let r = await sshExecSafe(mcfg, 'ls -lh /root/wallet_bot2.tar.gz', 'Main-Verify');
  console.log(r.stdout.trim());

  r = await sshExecSafe(mcfg, 
    'cd /root && tar xzf wallet_bot2.tar.gz && ls -d /root/Personal-Wallet-Tele-Bot-2 && echo "EXTRACTED OK"',
    'Main-Extract');
  console.log(r.stdout.trim());

  r = await sshExecSafe(mcfg,
    'mv /root/Personal-Wallet-Tele-Bot-2 /root/YYO-Personal-Wallet && echo "RENAMED to /root/YYO-Personal-Wallet" && ls -la /root/YYO-Personal-Wallet/ | head -25',
    'Main-Rename');
  console.log(r.stdout);

  // ============ STEP 6: Search old references ============
  console.log('\n📦 STEP 6: Search for old name references');
  r = await sshExecSafe(mcfg,
    'grep -rl "Personal-Wallet-Tele-Bot-2" /root/YYO-Personal-Wallet/ 2>/dev/null || echo "(none found)"',
    'Main-Grep');
  console.log('Old references:', r.stdout.trim());

  // ============ STEP 7: Check bot structure ============
  console.log('\n📦 STEP 7: Check bot structure');
  r = await sshExecSafe(mcfg,
    `echo "---VENV---" && if [ -f /root/YYO-Personal-Wallet/venv/bin/python ]; then /root/YYO-Personal-Wallet/venv/bin/python --version 2>&1; elif [ -f /root/YYO-Personal-Wallet/venv/bin/python3 ]; then /root/YYO-Personal-Wallet/venv/bin/python3 --version 2>&1; else echo "NO venv found"; fi && echo "---FILES---" && find /root/YYO-Personal-Wallet -maxdepth 1 -type f -o -maxdepth 1 -type d | sort && echo "---MAIN.PY---" && cat /root/YYO-Personal-Wallet/main.py`,
    'Main-Check');
  console.log(r.stdout);

  // ============ STEP 8: Check existing services/Nova ============
  console.log('\n📦 STEP 8: Check Main VPS environment');
  r = await sshExecSafe(mcfg,
    `echo "=== Docker ps ===" && docker ps --format '{{.Names}} {{.Image}} {{.Status}}' 2>/dev/null && echo "=== Wallet services ===" && systemctl list-units --type=service --all | grep -i wallet 2>/dev/null || echo "None" && echo "=== Nova containers ===" && docker ps --format '{{.Names}}' | grep -i nova 2>/dev/null || echo "None"`,
    'Main-Env');
  console.log(r.stdout);

  // ============ STEP 9: Create systemd service ============
  console.log('\n📦 STEP 9: Create systemd service');
  const serviceFile = `[Unit]
Description=YYO's Personal Wallet Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/YYO-Personal-Wallet
ExecStart=/root/YYO-Personal-Wallet/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target`;

  const fs = require('fs');
  const tmpSvc = path.join(os.tmpdir(), 'yyo-personal-wallet.service');
  fs.writeFileSync(tmpSvc, serviceFile);

  await sftpPut(mcfg, tmpSvc, '/etc/systemd/system/yyo-personal-wallet.service', 'Svc-Upload');
  await sleep(1000);
  fs.unlinkSync(tmpSvc);

  r = await sshExecSafe(mcfg, 'cat /etc/systemd/system/yyo-personal-wallet.service', 'Svc-Verify');
  console.log('Service file:');
  console.log(r.stdout);

  // ============ STEP 10: Setup Nova access ============
  console.log('\n📦 STEP 10: Setup Nova access');
  r = await sshExecSafe(mcfg,
    `chmod -R 755 /root/YYO-Personal-Wallet/ && echo "Permissions: 755" && mkdir -p /opt && ln -sf /root/YYO-Personal-Wallet /opt/yyo-personal-wallet && echo "Symlink: /opt/yyo-personal-wallet -> /root/YYO-Personal-Wallet" && ls -la /opt/yyo-personal-wallet`,
    'Nova-Setup');
  console.log(r.stdout);

  // Check Nova container
  r = await sshExecSafe(mcfg,
    `echo "=== Nova containers ===" && docker ps -a --format '{{.Names}} {{.Image}} {{.Status}}' | grep -i nova 2>/dev/null || echo "No nova container found" && echo "=== Inspect ===" && for c in oc-nova openclaw-nova; do echo "--- \$c ---"; docker inspect \$c 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin)[0]; print('Mounts:', json.dumps([m for m in d.get('Mounts',[])], indent=2)); print('Binds:', d.get('HostConfig',{}).get('Binds',[]))" 2>/dev/null || echo "  not found"; done`,
    'Nova-Inspect');
  console.log(r.stdout);

  // ============ STEP 11: Enable & Start ============
  console.log('\n📦 STEP 11: Enable and start service');
  r = await sshExecSafe(mcfg,
    'systemctl daemon-reload && systemctl enable yyo-personal-wallet && systemctl start yyo-personal-wallet && sleep 3 && systemctl status yyo-personal-wallet --no-pager -l',
    'Main-Start');
  console.log(r.stdout);

  // ============ STEP 12: Logs ============
  console.log('\n📦 STEP 12: Service logs');
  await sleep(2000);
  r = await sshExecSafe(mcfg,
    'journalctl -u yyo-personal-wallet --no-pager -n 40 2>/dev/null || echo "No journalctl output"',
    'Main-Logs');
  console.log(r.stdout);

  // ============ STEP 13: Cleanup ============
  console.log('\n📦 STEP 13: Cleanup');
  r = await sshExecSafe(mcfg, 'rm -f /root/wallet_bot2.tar.gz && echo "Cleaned up"', 'Main-Cleanup');
  console.log(r.stdout.trim());

  console.log('\n\n✅ MIGRATION COMPLETE');
  console.log('Bot: /root/YYO-Personal-Wallet');
  console.log('Service: yyo-personal-wallet');
  console.log('Symlink: /opt/yyo-personal-wallet');
}

main().catch(err => {
  console.error('\n❌ ERROR:', err.message || err);
  process.exit(1);
});
