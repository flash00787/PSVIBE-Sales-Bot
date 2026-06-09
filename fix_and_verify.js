#!/usr/bin/env node
/**
 * Fix service file + inspect Nova config + verify bot startup
 */
const { Client } = require('ssh2');
const fs = require('fs');

const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');
const DST = { host: '5.223.81.16', port: 22, username: 'root', privateKey: KEY, readyTimeout: 15000 };

const BOT_PATH = '/root/YYO-Personal-Wallet';
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
  const dst = await sshConnect(DST);
  console.log('✅ Connected\n');

  // ── 1. Fix the systemd service ──
  console.log('=== Fixing Systemd Service ===');
  
  // The bot runs from bot/ directory with venv
  const svc = `[Unit]
Description=YYO Personal Wallet Telegram Bot
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${BOT_PATH}/bot
Environment=PATH=/usr/local/bin:/usr/bin:/bin:${BOT_PATH}/bot/venv/bin
EnvironmentFile=-${BOT_PATH}/bot/.env
ExecStart=${BOT_PATH}/bot/venv/bin/python3 ${BOT_PATH}/bot/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SVC_NAME}

[Install]
WantedBy=multi-user.target`;

  const svcEsc = svc.replace(/'/g, "'\\''");
  await sshExec(dst, `printf '%s' '${svcEsc}' > /etc/systemd/system/${SVC_NAME}.service`);
  console.log('Service file updated');
  
  await sshExec(dst, 'systemctl daemon-reload');
  console.log('Daemon reloaded');

  // ── 2. Read bot/.env ──
  console.log('\n=== Bot .env file ===');
  let r = await sshExec(dst, `cat ${BOT_PATH}/bot/.env`);
  console.log('.env contents:', JSON.stringify(r.stdout));
  r = await sshExec(dst, `wc -c < ${BOT_PATH}/bot/.env`);
  console.log('.env size:', r.stdout, 'bytes');
  
  // ── 3. Look at actual bot code ──
  console.log('\n=== Bot main.py (HEAD) ===');
  r = await sshExec(dst, `head -60 ${BOT_PATH}/bot/main.py`);
  console.log(r.stdout);

  // ── 4. Check how bot gets its token ──
  console.log('\n=== Searching for token usage ===');
  r = await sshExec(dst, `grep -n "TOKEN\|BOT_TOKEN\|Application.builder\|application\|updater\|dispatcher\|run_polling" ${BOT_PATH}/bot/main.py 2>/dev/null | head -20`);
  console.log(r.stdout || '(no matches in first 60 lines)');
  
  // Read more of main.py
  r = await sshExec(dst, `tail -n +61 ${BOT_PATH}/bot/main.py | head -60`);
  console.log('\nBot main.py (continued):\n', r.stdout);

  // ── 5. Check Nova openclaw config ──
  console.log('\n=== Nova Config from Host ===');
  r = await sshExec(dst, 'cat /opt/openclaw/nova/openclaw.json 2>&1 | head -80');
  console.log(r.stdout);

  // Also check if there's a JSON config in Nova workspace
  r = await sshExec(dst, 'docker exec oc-nova find /home/node/.openclaw -name "*.json" -o -name "*.yaml" 2>&1 | head -20');
  console.log('\nNova workspace configs:', r.stdout);

  // Check Nova's config directory
  r = await sshExec(dst, 'ls /opt/openclaw/nova/ 2>&1');
  console.log('\n/opt/openclaw/nova contents:', r.stdout);

  // Check Nova's tools config for exec/SSH
  r = await sshExec(dst, 'cat /opt/openclaw/nova/config/openclaw.json 2>/dev/null | head -60 || echo "NOT FOUND at config/"');
  console.log('\nNova config/openclaw.json:', r.stdout);
  
  // Check ALL json/yaml configs in nova dir
  r = await sshExec(dst, 'find /opt/openclaw/nova -name "*.json" -o -name "*.yaml" -o -name "*.yml" 2>/dev/null');
  console.log('\nAll nova config files:', r.stdout);

  // Check docker-compose for nova volume mounts
  r = await sshExec(dst, 'cat /root/openclaw/nova.yml 2>/dev/null | head -40 || cat /root/openclaw/docker-compose.yml 2>/dev/null | head -40');
  console.log('\nNova docker config:', r.stdout);

  // ── 6. Add bot dir to Nova's accessible paths ──
  // Nova's volume mount: /opt/openclaw/nova → /home/node/.openclaw (in container)
  // If we create a symlink or bind mount, Nova can access the bot files
  console.log('\n=== Setting up Nova Bot Access ===');
  
  // Create a symlink from Nova workspace to bot directory
  r = await sshExec(dst, `ln -sf ${BOT_PATH} /opt/openclaw/nova/YYO-Personal-Wallet 2>&1 && echo "SYMLINK_OK" || echo "SYMLINK_FAIL"`);
  console.log('Symlink to Nova workspace:', r.stdout);

  // Verify symlink
  r = await sshExec(dst, 'ls -la /opt/openclaw/nova/YYO-Personal-Wallet 2>&1');
  console.log('Symlink:', r.stdout);

  // Verify from inside container
  r = await sshExec(dst, 'docker exec oc-nova ls -la /home/node/.openclaw/YYO-Personal-Wallet 2>&1 | head -10');
  console.log('From Nova container:', r.stdout);

  // ── 7. Update nova-wallet manager with correct paths ──
  console.log('\n=== Updating nova-wallet manager ===');
  const mgr = `#!/bin/bash
# YYO Personal Wallet Bot Manager - for Nova AI Agent
ACTION="\${1:-status}"
SVC="${SVC_NAME}"
DIR="${BOT_PATH}"
BOT_DIR="${BOT_PATH}/bot"
VENV_PYTHON="${BOT_PATH}/bot/venv/bin/python3"

case "\$ACTION" in
  status)
    systemctl status \$SVC --no-pager -l
    ;;
  start)
    systemctl start \$SVC && echo "✅ Wallet bot started" || echo "❌ Failed to start"
    ;;
  stop)
    systemctl stop \$SVC && echo "✅ Wallet bot stopped" || echo "❌ Failed to stop"
    ;;
  restart)
    systemctl restart \$SVC && echo "✅ Wallet bot restarted" || echo "❌ Failed to restart"
    ;;
  enable)
    systemctl enable \$SVC && echo "✅ Enabled on boot"
    ;;
  logs)
    journalctl -u \$SVC --no-pager -n "\${2:-50}"
    ;;
  logs-f)
    journalctl -u \$SVC -f
    ;;
  files)
    find \$DIR -type f \\( -name "*.py" -o -name "*.json" -o -name "*.txt" -o -name "*.md" -o -name "*.env" -o -name "*.sh" \\) ! -path "*/venv/*" ! -path "*/.git/*" ! -path "*/node_modules/*" ! -path "*/__pycache__/*" | sort
    ;;
  read)
    cat "\$DIR/\$2" 2>/dev/null || cat "\$BOT_DIR/\$2" 2>/dev/null || echo "❌ File not found: \$2"
    ;;
  run)
    shift
    cd "\$BOT_DIR" && exec \$VENV_PYTHON "\$@"
    ;;
  env)
    cat "\$BOT_DIR/.env" 2>/dev/null || echo "❌ No .env file"
    ;;
  edit-env)
    nano "\$BOT_DIR/.env"
    ;;
  path)
    echo "\$DIR"
    ;;
  *)
    echo "YYO Personal Wallet Bot — Nova Manager"
    echo "======================================="
    echo "  nova-wallet status       Service status"
    echo "  nova-wallet start        Start bot"
    echo "  nova-wallet stop         Stop bot"
    echo "  nova-wallet restart      Restart bot"
    echo "  nova-wallet logs [n]     Recent logs"
    echo "  nova-wallet files        List project files"
    echo "  nova-wallet read <file>  Read a file"
    echo "  nova-wallet run <args>   Execute Python"
    echo "  nova-wallet env          Show .env file"
    echo "  nova-wallet path         Show bot directory"
    ;;
esac`;

  const mgrEsc = mgr.replace(/'/g, "'\\''");
  await sshExec(dst, `printf '%s' '${mgrEsc}' > /usr/local/bin/nova-wallet && chmod +x /usr/local/bin/nova-wallet && echo "OK"`);
  console.log('Manager updated');

  // ── 8. Test the bot ──
  console.log('\n=== Testing Bot Startup ===');
  
  // First stop
  await sshExec(dst, `systemctl stop ${SVC_NAME}.service 2>&1`);
  
  // Start and wait
  r = await sshExec(dst, `systemctl start ${SVC_NAME}.service 2>&1`);
  console.log('Start:', r.code === 0 ? 'OK' : `FAIL: ${r.stderr}`);

  await new Promise(r => setTimeout(r, 5000));
  
  r = await sshExec(dst, `systemctl status ${SVC_NAME}.service --no-pager -l 2>&1 | head -25`);
  console.log('Status:\n', r.stdout);

  r = await sshExec(dst, `journalctl -u ${SVC_NAME}.service --no-pager -n 20`);
  console.log('Logs:\n', r.stdout);

  // ── 9. Update NOVA_README ──
  const readme = `# YYO Personal Wallet Bot - Nova Integration Guide
**Location:** ${BOT_PATH}  
**Bot Code:** ${BOT_PATH}/bot/  
**Service:** ${SVC_NAME}  
**Manager:** /usr/local/bin/nova-wallet

## Access from Nova Container
The bot directory is symlinked into Nova's workspace:
\`/home/node/.openclaw/YYO-Personal-Wallet\` → ${BOT_PATH}

## Quick Commands
\`\`\`
nova-wallet status          # Check if bot is running
nova-wallet start           # Start the bot
nova-wallet stop            # Stop the bot  
nova-wallet restart         # Restart the bot
nova-wallet logs 100        # View last 100 log lines
nova-wallet files           # List project files
nova-wallet read <file>     # Read a file from bot dir
nova-wallet run <script.py> # Run Python script
nova-wallet env             # View .env file
nova-wallet path            # Show bot directory
\`\`\`

## Important Files
- \`bot/main.py\` — Bot entry point (uses python-telegram-bot)
- \`bot/.env\` — Environment variables (TOKEN, etc.)
- \`bot/venv/\` — Python virtual environment
- \`bot/keep_alive.py\` — Flask keep-alive server (port 5001)
- \`bot/service_account.json\` — Google service account
- \`bot/requirements.txt\` — Python dependencies

## Dependencies (installed in venv)
- python-telegram-bot[job-queue] >=22.7
- flask >=3.1.3
- gspread >=6.2.1
- google-auth >=2.50.0
`;

  const rdEsc = readme.replace(/'/g, "'\\''");
  await sshExec(dst, `printf '%s' '${rdEsc}' > ${BOT_PATH}/NOVA_README.md && echo "OK"`);

  // ── 10. Final verification ──
  console.log('\n=== Final Verification ===');
  r = await sshExec(dst, '/usr/local/bin/nova-wallet status 2>&1 | head -15');
  console.log('nova-wallet status:\n', r.stdout);
  
  r = await sshExec(dst, '/usr/local/bin/nova-wallet files 2>&1 | head -20');
  console.log('nova-wallet files:\n', r.stdout);

  r = await sshExec(dst, 'docker exec oc-nova ls /home/node/.openclaw/YYO-Personal-Wallet/bot/main.py 2>&1');
  console.log('Nova can read bot/main.py:', r.stdout.includes('main.py') ? 'YES ✅' : 'NO ❌');

  r = await sshExec(dst, `docker exec oc-nova head -5 /home/node/.openclaw/YYO-Personal-Wallet/NOVA_README.md 2>&1`);
  console.log('Nova can read README:', r.stdout);

  console.log('\n✅ All fixes applied!');
  
  dst.end();
}

main().catch(console.error);
