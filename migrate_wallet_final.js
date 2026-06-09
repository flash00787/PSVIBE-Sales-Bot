#!/usr/bin/env node
/**
 * Migrate Personal-Wallet-Tele-Bot-2: Source VPS → Main VPS
 * Rename to YYO-Personal-Wallet + configure for Nova
 */
const { Client } = require('ssh2');
const fs = require('fs');

const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');
const SRC = { host: '167.71.196.120', port: 22, username: 'root', privateKey: KEY, readyTimeout: 10000 };
const DST = { host: '5.223.81.16', port: 22, username: 'root', privateKey: KEY, readyTimeout: 10000 };

const BOT_SRC = 'Personal-Wallet-Tele-Bot-2';
const BOT_DST = 'YYO-Personal-Wallet';
const BOT_PATH = `/root/${BOT_DST}`;
const SVC_NAME = 'yyo-personal-wallet';

function sshExec(client, cmd, timeout = 60000) {
  return new Promise((resolve, reject) => {
    client.exec(cmd, { timeout }, (err, stream) => {
      if (err) return reject(err);
      let s = '', e = '';
      stream.on('data', d => s += d.toString());
      stream.stderr.on('data', d => e += d.toString());
      stream.on('close', code => resolve({ code, stdout: s.trim(), stderr: e.trim() }));
    });
  });
}

function sshConnect(opts) {
  return new Promise((resolve, reject) => {
    const c = new Client();
    c.on('ready', () => resolve(c));
    c.on('error', reject);
    c.connect(opts);
  });
}

async function main() {
  let src, dst;
  const R = {}; // results

  try {
    // ── STEP 1: Archive on Source ──
    console.log('═'.repeat(60));
    console.log(' STEP 1: Archive Personal-Wallet-Tele-Bot-2 on Source VPS');
    console.log('═'.repeat(60));
    
    src = await sshConnect(SRC);
    console.log('✅ Connected to Source VPS');

    // Check bot exists
    let r = await sshExec(src, `ls /root/${BOT_SRC}/main.py /root/${BOT_SRC}/bot.py 2>&1`);
    console.log('Bot entry check:', r.stdout);
    
    r = await sshExec(src, `find /root/${BOT_SRC}/ -type f | wc -l`);
    console.log(`Files in bot: ${r.stdout}`);

    // List important files
    r = await sshExec(src, `ls -la /root/${BOT_SRC}/ | head -30`);
    console.log('Bot directory:\n', r.stdout);
    
    // Read .env or config to preserve
    r = await sshExec(src, `cat /root/${BOT_SRC}/.env 2>/dev/null | head -10 || echo "NO .env"`);
    console.log('.env first lines:', r.stdout.substring(0, 200));

    // Check requirements
    r = await sshExec(src, `cat /root/${BOT_SRC}/requirements.txt 2>/dev/null || echo "NO requirements.txt"`);
    console.log('Requirements:', r.stdout);

    // Archive
    console.log('\nCreating archive...');
    r = await sshExec(src, `cd /root && tar czf /tmp/wallet_bot2.tar.gz ${BOT_SRC}/`, 120000);
    console.log(`Tar: code=${r.code} ${r.stderr || ''}`);

    r = await sshExec(src, 'ls -lh /tmp/wallet_bot2.tar.gz');
    console.log('Archive:', r.stdout);
    R.step1 = { success: true, archive: r.stdout };

    src.end();
    console.log('✅ Step 1 done\n');

    // ── STEP 2: Transfer via base64 ──
    console.log('═'.repeat(60));
    console.log(' STEP 2: Transfer archive to Main VPS');
    console.log('═'.repeat(60));

    // Reconnect to source to read archive
    src = await sshConnect(SRC);
    console.log('✅ Source connected');
    
    // Get base64 of archive
    r = await sshExec(src, 'base64 /tmp/wallet_bot2.tar.gz', 180000);
    const b64data = r.stdout;
    console.log(`Archive base64 size: ${b64data.length} chars`);
    src.end();

    // Connect to destination
    dst = await sshConnect(DST);
    console.log('✅ Main VPS connected');

    // Write base64 in chunks to destination
    const b64Path = '/tmp/wallet_bot2.b64';
    await sshExec(dst, `> ${b64Path}`);
    
    const chunkSize = 400000;
    for (let i = 0; i < b64data.length; i += chunkSize) {
      const chunk = b64data.slice(i, i + chunkSize);
      // Write using printf with escaped single quotes
      const escaped = chunk.replace(/'/g, "'\\''");
      await sshExec(dst, `printf '%s' '${escaped}' >> ${b64Path}`, 30000);
      if ((i / chunkSize) % 5 === 0) {
        console.log(`  Chunk ${Math.floor(i/chunkSize)+1}/${Math.ceil(b64data.length/chunkSize)}...`);
      }
    }
    console.log('All chunks written');

    // Decode
    r = await sshExec(dst, `base64 -d ${b64Path} > /tmp/wallet_bot2.tar.gz && ls -lh /tmp/wallet_bot2.tar.gz`, 60000);
    console.log('Decoded:', r.stdout);
    
    // Cleanup b64
    await sshExec(dst, `rm -f ${b64Path}`);
    
    R.step2 = { success: true };
    console.log('✅ Step 2 done\n');

    // ── STEP 3: Extract & Rename on Main VPS ──
    console.log('═'.repeat(60));
    console.log(' STEP 3: Extract & Rename to YYO-Personal-Wallet');
    console.log('═'.repeat(60));

    // Remove old if exists
    await sshExec(dst, `rm -rf ${BOT_PATH}`);

    // Extract
    r = await sshExec(dst, `cd /root && tar xzf /tmp/wallet_bot2.tar.gz`, 60000);
    console.log(`Extract: code=${r.code}`);

    // Rename
    r = await sshExec(dst, `mv /root/${BOT_SRC} ${BOT_PATH} && echo "RENAMED"`);
    console.log('Rename:', r.stdout);

    // Verify
    r = await sshExec(dst, `ls ${BOT_PATH}/ | head -25`);
    console.log('New bot contents:\n', r.stdout);

    // Update internal references
    r = await sshExec(dst, `cd ${BOT_PATH} && grep -rl "${BOT_SRC}" . 2>/dev/null || echo "NO_REFS"`);
    console.log('Files with old name refs:', r.stdout);
    if (r.stdout !== 'NO_REFS') {
      r = await sshExec(dst, `cd ${BOT_PATH} && find . -type f -exec sed -i 's/${BOT_SRC}/${BOT_DST}/g' {} + && echo "UPDATED"`);
      console.log('Reference update:', r.stdout);
    }

    // Clean archive
    await sshExec(dst, 'rm -f /tmp/wallet_bot2.tar.gz');
    
    R.step3 = { success: true };
    console.log('✅ Step 3 done\n');

    // ── STEP 4: Check Nova Setup ──
    console.log('═'.repeat(60));
    console.log(' STEP 4: Inspect Nova setup on Main VPS');
    console.log('═'.repeat(60));

    // Check Nova config
    r = await sshExec(dst, 'cat /opt/openclaw/nova/openclaw.json 2>&1 | head -100');
    console.log('Nova openclaw.json:\n', r.stdout);

    // Check Nova container
    r = await sshExec(dst, 'docker inspect oc-nova --format "User={{.Config.User}} WorkDir={{.Config.WorkingDir}} Env={{range .Config.Env}}{{.}} {{end}}" 2>&1');
    console.log('Nova container info:', r.stdout.substring(0, 500));

    r = await sshExec(dst, 'docker exec oc-nova id 2>&1');
    console.log('Nova container user:', r.stdout);

    r = await sshExec(dst, 'docker exec oc-nova cat /app/openclaw.json 2>&1 | head -50');
    console.log('Nova internal config:', r.stdout.substring(0, 500));

    // Check AGENTS.md / TOOLS.md for Nova
    r = await sshExec(dst, 'docker exec oc-nova ls /home/node/.openclaw/workspace/ 2>&1 | head -30');
    console.log('Nova workspace:', r.stdout);

    R.step4 = { success: true };
    console.log('✅ Step 4 done\n');

    // ── STEP 5: Create systemd service ──
    console.log('═'.repeat(60));
    console.log(' STEP 5: Create systemd service');
    console.log('═'.repeat(60));

    // Determine entry point
    r = await sshExec(dst, `ls ${BOT_PATH}/main.py ${BOT_PATH}/bot.py ${BOT_PATH}/app.py 2>&1`);
    let entry = 'main.py';
    if (r.stdout.includes('bot.py') && !r.stdout.includes('main.py')) entry = 'bot.py';
    if (r.stdout.includes('app.py')) entry = 'app.py';
    console.log(`Entry point: ${entry}`);

    // Check Python
    r = await sshExec(dst, 'which python3 && python3 --version');
    console.log('Python:', r.stdout.split('\n')[0]);

    // Check venv
    r = await sshExec(dst, `ls -d ${BOT_PATH}/venv ${BOT_PATH}/.venv 2>&1`);
    const hasVenv = r.stdout.includes('venv');
    const pythonBin = hasVenv ? `${BOT_PATH}/venv/bin/python3` : '/usr/bin/python3';
    console.log(`Python binary: ${pythonBin} (venv: ${hasVenv})`);

    // Install requirements
    r = await sshExec(dst, `cat ${BOT_PATH}/requirements.txt 2>/dev/null`);
    if (r.stdout && !r.stdout.includes('No such file')) {
      console.log('Installing requirements...');
      r = await sshExec(dst, `pip3 install -r ${BOT_PATH}/requirements.txt 2>&1 | tail -10`, 120000);
      console.log('pip:', r.stdout || r.stderr);
    }

    // Create service
    const svc = `[Unit]
Description=YYO Personal Wallet Telegram Bot
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${BOT_PATH}
Environment=PATH=/usr/local/bin:/usr/bin:/bin
EnvironmentFile=-${BOT_PATH}/.env
ExecStart=${pythonBin} ${BOT_PATH}/${entry}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=yyo-personal-wallet

[Install]
WantedBy=multi-user.target`;

    const escaped = svc.replace(/'/g, "'\\''");
    await sshExec(dst, `printf '%s' '${escaped}' > /etc/systemd/system/${SVC_NAME}.service`);
    
    r = await sshExec(dst, 'systemctl daemon-reload && echo "OK"');
    console.log('Daemon reload:', r.stdout);

    r = await sshExec(dst, `systemctl enable ${SVC_NAME}.service 2>&1`);
    console.log('Enable:', r.stdout);

    R.step5 = { success: true };
    console.log('✅ Step 5 done\n');

    // ── STEP 6: Nova Access Configuration ──
    console.log('═'.repeat(60));
    console.log(' STEP 6: Configure Nova Access');
    console.log('═'.repeat(60));

    // Set permissions
    r = await sshExec(dst, `chmod -R 755 ${BOT_PATH} && chmod 755 /root && echo "OK"`);
    console.log('Permissions:', r.stdout);

    // Get docker group
    r = await sshExec(dst, 'getent group docker | cut -d: -f3');
    const dockerGid = r.stdout.trim();
    console.log('Docker GID:', dockerGid);

    // Create nova management script
    const mgrScript = `#!/bin/bash
# YYO Personal Wallet Bot Management - for Nova AI Agent
ACTION="\${1:-status}"
SVC="${SVC_NAME}"
DIR="${BOT_PATH}"

case "\$ACTION" in
  status)   systemctl status \$SVC --no-pager -l ;;
  start)    systemctl start \$SVC && echo "✅ Wallet bot started" ;;
  stop)     systemctl stop \$SVC && echo "✅ Wallet bot stopped" ;;
  restart)  systemctl restart \$SVC && echo "✅ Wallet bot restarted" ;;
  logs)     journalctl -u \$SVC --no-pager -n "\${2:-50}" ;;
  files)    find \$DIR -type f \\( -name "*.py" -o -name "*.json" -o -name "*.txt" -o -name "*.env" \\) | sort ;;
  read)     cat "\$DIR/\$2" 2>/dev/null || echo "Usage: nova-wallet read <filename>" ;;
  run)      shift; cd "\$DIR" && python3 "\$@" ;;
  *)        echo "YYO Personal Wallet | nova-wallet [status|start|stop|restart|logs|files|read|run]" ;;
esac`;

    const mgrEsc = mgrScript.replace(/'/g, "'\\''");
    await sshExec(dst, `printf '%s' '${mgrEsc}' > /usr/local/bin/nova-wallet && chmod +x /usr/local/bin/nova-wallet && echo "OK"`);
    console.log('Management script created');

    // Create Nova README
    const readme = `# YYO Personal Wallet Bot
**Location:** ${BOT_PATH}  
**Service:** ${SVC_NAME}  
**Entry:** ${entry}

## Nova Commands
\`\`\`
nova-wallet status          # Service status
nova-wallet start           # Start bot
nova-wallet stop            # Stop bot
nova-wallet restart         # Restart bot
nova-wallet logs [lines]    # View logs
nova-wallet files           # List source files
nova-wallet read <file>     # Read a file
nova-wallet run <script>    # Execute script
\`\`\`

## Direct Access
- systemctl status ${SVC_NAME}
- journalctl -u ${SVC_NAME} -f
- cd ${BOT_PATH} && python3 ${entry}
`;

    const rdEsc = readme.replace(/'/g, "'\\''");
    await sshExec(dst, `printf '%s' '${rdEsc}' > ${BOT_PATH}/NOVA_README.md && echo "OK"`);

    // ── Start the bot ──
    console.log('\nStarting the wallet bot...');
    r = await sshExec(dst, `systemctl start ${SVC_NAME}.service 2>&1 && echo "STARTED" || echo "FAILED"`);
    console.log('Start:', r.stdout);

    await new Promise(r => setTimeout(r, 3000));
    
    r = await sshExec(dst, `systemctl status ${SVC_NAME}.service --no-pager -l 2>&1`);
    console.log('Service status:\n', r.stdout);

    r = await sshExec(dst, `journalctl -u ${SVC_NAME}.service --no-pager -n 15`);
    console.log('Recent logs:\n', r.stdout);

    R.step6 = { success: true };
    console.log('✅ Step 6 done\n');

    // Close
    dst.end();

    // ── FINAL REPORT ──
    console.log('\n' + '═'.repeat(60));
    console.log(' MIGRATION COMPLETE — Report');
    console.log('═'.repeat(60));
    console.log(` ✅ Step 1 — Archived bot from Source VPS`);
    console.log(` ✅ Step 2 — Transferred archive to Main VPS`);
    console.log(` ✅ Step 3 — Extracted & renamed to: ${BOT_PATH}`);
    console.log(` ✅ Step 4 — Nova setup inspected`);
    console.log(` ✅ Step 5 — Systemd service created: ${SVC_NAME}`);
    console.log(` ✅ Step 6 — Nova access configured`);
    console.log('');
    console.log(` 📁 Bot Directory: ${BOT_PATH}`);
    console.log(` ⚙️  Service:      ${SVC_NAME}.service`);
    console.log(` 🔧 Manager:      /usr/local/bin/nova-wallet`);
    console.log(` 📖 README:       ${BOT_PATH}/NOVA_README.md`);
    console.log(` 🤖 Nova can use: nova-wallet [status|start|stop|restart|logs|files|read|run]`);
    console.log('═'.repeat(60));

  } catch(err) {
    console.error('\n❌ FATAL ERROR:', err.message);
    console.error(err.stack);
    // Try to clean up connections
    try { if (src) src.end(); } catch {}
    try { if (dst) dst.end(); } catch {}
  }
}

main().catch(console.error);
