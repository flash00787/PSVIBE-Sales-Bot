const { Client } = require('ssh2');
const { readFileSync } = require('fs');
const path = require('path');
const os = require('os');

const SOURCE_HOST = '167.71.196.120';
const SOURCE_USER = 'root';
const SOURCE_PASS = 'Freedom2024#RevFlash';

const MAIN_HOST = '5.223.81.16';
const MAIN_USER = 'root';
const MAIN_KEY = readFileSync(path.join(__dirname, '.ssh', 'id_rsa'));

// Helper: exec over SSH
function sshExec(connConfig, command, label) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let stdout = '', stderr = '';
    conn.on('ready', () => {
      console.log(`\n=== [${label}] Connected. Executing: ${command.substring(0, 80)}...`);
      conn.exec(command, (err, stream) => {
        if (err) { conn.end(); return reject(err); }
        stream.on('data', d => { stdout += d.toString(); });
        stream.stderr.on('data', d => { stderr += d.toString(); });
        stream.on('close', (code) => {
          conn.end();
          console.log(`[${label}] OK (exit ${code})`);
          resolve({ stdout, stderr, code });
        });
      });
    });
    conn.on('error', e => { conn.end(); reject(e); });
    conn.connect(connConfig);
  });
}

// SFTP get file from remote to local
function sftpGet(connConfig, remotePath, localPath, label) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      console.log(`\n=== [${label}] SFTP GET: ${remotePath} -> ${localPath}`);
      conn.sftp((err, sftp) => {
        if (err) { conn.end(); return reject(err); }
        const ws = require('fs').createWriteStream(localPath);
        const rs = sftp.createReadStream(remotePath);
        let bytes = 0;
        rs.on('data', d => { bytes += d.length; if (bytes % (5*1024*1024) < 65536) process.stdout.write('.'); });
        rs.on('end', () => {
          ws.end();
          console.log(`\n[${label}] Downloaded ${(bytes/1024/1024).toFixed(1)} MB`);
          conn.end();
          resolve(bytes);
        });
        rs.on('error', e => { conn.end(); reject(e); });
        rs.pipe(ws);
      });
    });
    conn.on('error', e => { conn.end(); reject(e); });
    conn.connect(connConfig);
  });
}

// SFTP put file from local to remote
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
      });
    });
    conn.on('error', e => { conn.end(); reject(e); });
    conn.connect(connConfig);
  });
}

async function main() {
  console.log('🚀 Personal-Wallet-Tele-Bot-2 Migration Script (SFTP)');
  console.log('======================================================\n');

  const tmpFile = path.join(os.tmpdir(), 'wallet_bot2.tar.gz');

  // ============ STEP 1: Check Source VPS ============
  console.log('\n📦 STEP 1: Check Source VPS for Personal-Wallet-Tele-Bot-2');
  const lsResult = await sshExec(
    { host: SOURCE_HOST, port: 22, username: SOURCE_USER, password: SOURCE_PASS },
    'ls -la /root/Personal-Wallet-Tele-Bot-2/ 2>&1',
    'Source-LS'
  );
  console.log(lsResult.stdout.slice(0, 2000));

  // ============ STEP 2: Archive on Source VPS ============
  console.log('\n📦 STEP 2: Archive bot on Source VPS');
  const archiveResult = await sshExec(
    { host: SOURCE_HOST, port: 22, username: SOURCE_USER, password: SOURCE_PASS },
    'cd /root && tar czf /tmp/wallet_bot2.tar.gz Personal-Wallet-Tele-Bot-2/ && ls -lh /tmp/wallet_bot2.tar.gz',
    'Source-Archive'
  );
  console.log(archiveResult.stdout.trim());

  // ============ STEP 3: SFTP Download to local temp ============
  console.log('\n📦 STEP 3: SFTP Download from Source VPS to local temp');
  const downloadBytes = await sftpGet(
    { host: SOURCE_HOST, port: 22, username: SOURCE_USER, password: SOURCE_PASS },
    '/tmp/wallet_bot2.tar.gz',
    tmpFile,
    'Source-SFTP-DL'
  );

  // ============ STEP 4: SFTP Upload to Main VPS ============
  console.log('\n📦 STEP 4: SFTP Upload to Main VPS');
  const uploadBytes = await sftpPut(
    { host: MAIN_HOST, port: 22, username: MAIN_USER, privateKey: MAIN_KEY },
    tmpFile,
    '/root/wallet_bot2.tar.gz',
    'Main-SFTP-UL'
  );

  // Clean up local temp file
  require('fs').unlinkSync(tmpFile);
  console.log('Cleaned up local temp file');

  // ============ STEP 5: Extract & Rename on Main VPS ============
  console.log('\n📦 STEP 5: Extract and rename on Main VPS');
  const extractResult = await sshExec(
    { host: MAIN_HOST, port: 22, username: MAIN_USER, privateKey: MAIN_KEY },
    `cd /root && tar xzf wallet_bot2.tar.gz && ls -la /root/Personal-Wallet-Tele-Bot-2/ | head -20 && mv /root/Personal-Wallet-Tele-Bot-2 /root/YYO-Personal-Wallet && echo "RENAMED to /root/YYO-Personal-Wallet" && ls -la /root/YYO-Personal-Wallet/ | head -20`,
    'Main-Extract'
  );
  console.log(extractResult.stdout.slice(0, 3000));

  // ============ STEP 6: Search/replace references ============
  console.log('\n📦 STEP 6: Search for old name references');
  const grepResult = await sshExec(
    { host: MAIN_HOST, port: 22, username: MAIN_USER, privateKey: MAIN_KEY },
    `grep -rl "Personal-Wallet-Tele-Bot-2" /root/YYO-Personal-Wallet/ 2>/dev/null || echo "(none found)"`,
    'Main-Grep'
  );
  console.log('Old references:', grepResult.stdout.trim());

  // ============ STEP 7: Check bot structure ============
  console.log('\n📦 STEP 7: Check bot structure / venv');
  const checkResult = await sshExec(
    { host: MAIN_HOST, port: 22, username: MAIN_USER, privateKey: MAIN_KEY },
    `if [ -f /root/YYO-Personal-Wallet/venv/bin/python ]; then echo "venv python: $("$(/root/YYO-Personal-Wallet/venv/bin/python --version 2>&1)")"; elif [ -f /root/YYO-Personal-Wallet/venv/bin/python3 ]; then echo "venv python3: $("$(/root/YYO-Personal-Wallet/venv/bin/python3 --version 2>&1)")"; else echo "NO venv found"; fi && echo "---FILES---" && find /root/YYO-Personal-Wallet -maxdepth 1 -type f | sort && echo "---MAIN.PY---" && cat /root/YYO-Personal-Wallet/main.py`,
    'Main-Check'
  );
  console.log(checkResult.stdout);

  // ============ STEP 8: Check for existing bots/running services ============
  console.log('\n📦 STEP 8: Check Main VPS existing services');
  const svcCheckResult = await sshExec(
    { host: MAIN_HOST, port: 22, username: MAIN_USER, privateKey: MAIN_KEY },
    `echo "=== Running services ===" && systemctl list-units --type=service --state=running | grep -i wallet && echo "=== Systemd services ===" && ls /etc/systemd/system/ | grep -i wallet && echo "=== Docker containers ===" && docker ps --format '{{.Names}}' 2>/dev/null`,
    'Main-Services'
  );
  console.log(svcCheckResult.stdout);

  // ============ STEP 9: Setup systemd service ============
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

  await sftpPut(
    { host: MAIN_HOST, port: 22, username: MAIN_USER, privateKey: MAIN_KEY },
    tmpSvc,
    '/etc/systemd/system/yyo-personal-wallet.service',
    'Main-Svc-Upload'
  );
  fs.unlinkSync(tmpSvc);

  const svcVerify = await sshExec(
    { host: MAIN_HOST, port: 22, username: MAIN_USER, privateKey: MAIN_KEY },
    'cat /etc/systemd/system/yyo-personal-wallet.service',
    'Main-Svc-Verify'
  );
  console.log(svcVerify.stdout);

  // ============ STEP 10: Setup Nova access ============
  console.log('\n📦 STEP 10: Setup Nova access');
  const novaResult = await sshExec(
    { host: MAIN_HOST, port: 22, username: MAIN_USER, privateKey: MAIN_KEY },
    `chmod -R 755 /root/YYO-Personal-Wallet/ && echo "Permissions set" && mkdir -p /opt && ln -sf /root/YYO-Personal-Wallet /opt/yyo-personal-wallet && echo "Symlink created: /opt/yyo-personal-wallet -> /root/YYO-Personal-Wallet" && echo "---DOCKER PS---" && docker ps --format '{{.Names}} {{.Image}}' 2>/dev/null && echo "---DOCKER INSPECT---" && (docker inspect oc-nova 2>/dev/null && echo "oc-nova found" || echo "oc-nova not found, trying openclaw-nova" && (docker inspect openclaw-nova 2>/dev/null && echo "openclaw-nova found" || echo "No Nova container found"))`,
    'Main-Nova'
  );
  console.log(novaResult.stdout);

  // ============ STEP 11: Enable & Start service ============
  console.log('\n📦 STEP 11: Enable and start service');
  const startResult = await sshExec(
    { host: MAIN_HOST, port: 22, username: MAIN_USER, privateKey: MAIN_KEY },
    `systemctl daemon-reload && systemctl enable yyo-personal-wallet && systemctl start yyo-personal-wallet && sleep 3 && systemctl status yyo-personal-wallet --no-pager -l`,
    'Main-Start'
  );
  console.log(startResult.stdout);

  // ============ STEP 12: Follow-up log check ============
  console.log('\n📦 STEP 12: Check service logs');
  const logResult = await sshExec(
    { host: MAIN_HOST, port: 22, username: MAIN_USER, privateKey: MAIN_KEY },
    `journalctl -u yyo-personal-wallet --no-pager -n 30 2>/dev/null || echo "No journalctl output"`,
    'Main-Logs'
  );
  console.log(logResult.stdout);

  // ============ STEP 13: Cleanup ============
  console.log('\n📦 STEP 13: Cleanup');
  await sshExec(
    { host: SOURCE_HOST, port: 22, username: SOURCE_USER, password: SOURCE_PASS },
    'rm -f /tmp/wallet_bot2.tar.gz && echo "Cleaned up source"',
    'Source-Cleanup'
  );
  await sshExec(
    { host: MAIN_HOST, port: 22, username: MAIN_USER, privateKey: MAIN_KEY },
    'rm -f /root/wallet_bot2.tar.gz && echo "Cleaned up main"',
    'Main-Cleanup'
  );

  console.log('\n\n✅ MIGRATION COMPLETE');
  console.log('================================');
  console.log('Bot: /root/YYO-Personal-Wallet');
  console.log('Service: yyo-personal-wallet');
  console.log('Symlink: /opt/yyo-personal-wallet');
  console.log('================================\n');
}

main().catch(err => {
  console.error('\n❌ ERROR:', err.message || err);
  process.exit(1);
});
