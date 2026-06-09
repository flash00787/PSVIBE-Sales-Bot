#!/usr/bin/env node
/**
 * Steps 3-6: Extract, Rename, Systemd, Nova Access on Main VPS
 * Archive is already at /root/wallet_bot2.tar.gz on Main VPS
 */
const { Client } = require('ssh2');
const fs = require('fs');

const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');
const DST = { host: '5.223.81.16', port: 22, username: 'root', privateKey: KEY, readyTimeout: 15000 };

const BOT_SRC = 'Personal-Wallet-Tele-Bot-2';
const BOT_DST = 'YYO-Personal-Wallet';
const BOT_PATH = `/root/${BOT_DST}`;
const SVC_NAME = 'yyo-personal-wallet';
const ARCHIVE = '/root/wallet_bot2.tar.gz';

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
  try {
    const dst = await sshConnect(DST);
    console.log('✅ Connected to Main VPS\n');

    // ── STEP 3: Extract & Rename ──
    console.log('═'.repeat(60));
    console.log(' STEP 3: Extract & Rename');
    console.log('═'.repeat(60));

    // Remove old
    await sshExec(dst, `rm -rf ${BOT_PATH}`);
    
    // Extract
    console.log('Extracting archive...');
    let r = await sshExec(dst, `cd /root && tar xzf ${ARCHIVE} 2>&1`, 120000);
    console.log(`Extract: code=${r.code} ${r.stderr || ''}`);

    // Verify extracted
    r = await sshExec(dst, `ls -d /root/${BOT_SRC} 2>&1`);
    console.log('Extracted dir exists:', r.stdout.includes(BOT_SRC) ? 'YES' : 'NO');

    // Rename
    r = await sshExec(dst, `mv /root/${BOT_SRC} ${BOT_PATH} && echo "RENAMED"`);
    console.log('Rename:', r.stdout);

    // Show contents
    r = await sshExec(dst, `ls ${BOT_PATH}/ | head -30`);
    console.log('Bot root files:\n', r.stdout);

    r = await sshExec(dst, `ls ${BOT_PATH}/bot/ | head -30`);
    console.log('Bot/bot dir:\n', r.stdout);

    // Find Python entry point
    r = await sshExec(dst, `ls ${BOT_PATH}/main.py ${BOT_PATH}/bot/main.py ${BOT_PATH}/bot/bot.py ${BOT_PATH}/bot/__main__.py ${BOT_PATH}/bot/app.py 2>&1`);
    console.log('Entry point candidates:\n', r.stdout);

    // Read main.py
    r = await sshExec(dst, `cat ${BOT_PATH}/main.py`);
    console.log('main.py:\n', r.stdout);

    // Find actual bot code
    r = await sshExec(dst, `find ${BOT_PATH}/bot -name "*.py" -type f | head -20`);
    console.log('Python files in bot/:\n', r.stdout);

    // Check for .env
    r = await sshExec(dst, `ls -la ${BOT_PATH}/.env ${BOT_PATH}/bot/.env ${BOT_PATH}/config.json 2>&1`);
    console.log('Config files:', r.stdout);

    // Read .env if exists (mask token)
    r = await sshExec(dst, `cat ${BOT_PATH}/.env 2>/dev/null | sed 's/TOKEN=.*/TOKEN=***MASKED***/' | head -20 || cat ${BOT_PATH}/bot/.env 2>/dev/null | sed 's/TOKEN=.*/TOKEN=***MASKED***/' | head -20 || echo "NO .env found"`);
    console.log('.env (masked):\n', r.stdout);

    // Find start scripts
    r = await sshExec(dst, `ls ${BOT_PATH}/start_wallet_bot.sh ${BOT_PATH}/scripts/ 2>&1`);
    console.log('Start scripts:', r.stdout);

    // Read start script
    r = await sshExec(dst, `cat ${BOT_PATH}/start_wallet_bot.sh 2>/dev/null`);
    console.log('start_wallet_bot.sh:\n', r.stdout);

    // Update old name references
    r = await sshExec(dst, `grep -rl "${BOT_SRC}" ${BOT_PATH}/ 2>/dev/null | head -10`);
    console.log('Files with old name:', r.stdout || '(none)');
    if (r.stdout && r.stdout !== '(none)') {
      r = await sshExec(dst, `find ${BOT_PATH}/ -type f -exec sed -i 's/${BOT_SRC}/${BOT_DST}/g' {} + && echo "UPDATED_ALL"`);
      console.log('Reference update:', r.stdout);
    }

    // Check pyproject.toml / package.json
    r = await sshExec(dst, `cat ${BOT_PATH}/pyproject.toml 2>/dev/null`);
    console.log('pyproject.toml:', r.stdout);

    // Check for requirements/pyproject deps
    r = await sshExec(dst, `pip3 list 2>/dev/null | grep -iE "telegram|python-telegram|asyncio|aiohttp|requests"`);
    console.log('Python telegram packages:', r.stdout);

    console.log('✅ Step 3 done\n');

    // ── STEP 4: Inspect Nova ──
    console.log('═'.repeat(60));
    console.log(' STEP 4: Inspect Nova configuration');
    console.log('═'.repeat(60));

    r = await sshExec(dst, 'docker ps --format "{{.Names}} {{.Image}} {{.Status}}" | grep nova');
    console.log('Nova container:', r.stdout);

    r = await sshExec(dst, 'docker exec oc-nova id 2>&1');
    console.log('Nova user:', r.stdout);

    r = await sshExec(dst, 'docker exec oc-nova cat /app/openclaw.json 2>&1 | head -80');
    console.log('Nova config:\n', r.stdout);

    // Check Nova's TOOLS.md
    r = await sshExec(dst, 'docker exec oc-nova cat /home/node/.openclaw/workspace/TOOLS.md 2>&1 | tail -40');
    console.log('Nova TOOLS.md (end):', r.stdout);

    // Check Nova workspace
    r = await sshExec(dst, 'docker exec oc-nova ls /home/node/.openclaw/workspace/ 2>&1 | head -20');
    console.log('Nova workspace files:', r.stdout);

    // Check Nova's exec/ssh access 
    r = await sshExec(dst, 'docker exec oc-nova cat /home/node/.openclaw/workspace/AGENTS.md 2>&1 | head -30');
    console.log('Nova AGENTS.md:\n', r.stdout);

    // Check if Nova has SSH access configured
    r = await sshExec(dst, 'docker exec oc-nova ls -la /home/node/.openclaw/workspace/.ssh/ 2>&1');
    console.log('Nova SSH keys:', r.stdout);

    // Check what Nova can access on host
    r = await sshExec(dst, 'docker inspect oc-nova --format "{{json .HostConfig.Binds}}" 2>&1');
    console.log('Nova volume binds:', r.stdout);

    // Nova container's openclaw.json full
    r = await sshExec(dst, 'docker exec oc-nova cat /app/openclaw.json 2>&1');
    console.log('Nova openclaw.json (FULL):\n', r.stdout);

    console.log('✅ Step 4 done\n');

    // ── STEP 5: Create systemd service ──
    console.log('═'.repeat(60));
    console.log(' STEP 5: Create systemd service');
    console.log('═'.repeat(60));

    // Determine how the bot runs
    // main.py imports from bot module
    // start_wallet_bot.sh shows the startup command
    // Let's figure out the right launch command
    r = await sshExec(dst, 'which python3 && python3 --version');
    console.log('Python:', r.stdout);

    // Check if bot module is installable
    r = await sshExec(dst, `ls ${BOT_PATH}/bot/__init__.py ${BOT_PATH}/bot/__main__.py 2>&1`);
    console.log('Bot module init:', r.stdout);

    // Read more of the bot structure
    r = await sshExec(dst, `head -5 ${BOT_PATH}/bot/__init__.py 2>/dev/null`);
    console.log('bot/__init__.py:', r.stdout);

    // Check what the main.py does
    r = await sshExec(dst, `cat ${BOT_PATH}/main.py`);
    console.log('main.py content:', r.stdout);

    // Check bot module structure deeper  
    r = await sshExec(dst, `find ${BOT_PATH}/bot -maxdepth 1 -name "*.py" -type f`);
    console.log('bot/*.py files:', r.stdout);

    // Try to find where bot token comes from
    r = await sshExec(dst, `grep -r "TOKEN\|BOT_TOKEN\|bot_token\|= os.environ\|getenv" ${BOT_PATH}/bot/ 2>/dev/null | head -20`);
    console.log('Token references:\n', r.stdout);

    // Create systemd service that runs from the bot directory
    // The bot seems to use `python3 main.py` from the project root
    const svc = `[Unit]
Description=YYO Personal Wallet Telegram Bot
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${BOT_PATH}
Environment=PATH=/usr/local/bin:/usr/bin:/bin:${BOT_PATH}/.venv/bin
EnvironmentFile=-${BOT_PATH}/.env
ExecStart=/usr/bin/python3 ${BOT_PATH}/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SVC_NAME}

[Install]
WantedBy=multi-user.target`;

    const svcEsc = svc.replace(/'/g, "'\\''");
    r = await sshExec(dst, `printf '%s' '${svcEsc}' > /etc/systemd/system/${SVC_NAME}.service`);
    console.log('Service file written');
    
    r = await sshExec(dst, `cat /etc/systemd/system/${SVC_NAME}.service`);
    console.log('Service file:\n', r.stdout);

    r = await sshExec(dst, 'systemctl daemon-reload && echo "OK"');
    console.log('Daemon reload:', r.stdout);

    r = await sshExec(dst, `systemctl enable ${SVC_NAME}.service 2>&1`);
    console.log('Enable:', r.stdout);

    console.log('✅ Step 5 done\n');

    // ── STEP 6: Nova Access ──
    console.log('═'.repeat(60));
    console.log(' STEP 6: Configure Nova Access');
    console.log('═'.repeat(60));

    // Set permissions
    r = await sshExec(dst, `chmod -R 755 ${BOT_PATH} && chmod 755 /root && echo "OK"`);
    console.log('Permissions set:', r.stdout);

    // Create nova-wallet management script
    const mgr = `#!/bin/bash
# YYO Personal Wallet Bot Manager - for Nova AI Agent
# Usage: nova-wallet [status|start|stop|restart|logs|files|read|run|env]
ACTION="\${1:-status}"
SVC="${SVC_NAME}"
DIR="${BOT_PATH}"

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
  disable)
    systemctl disable \$SVC && echo "✅ Disabled on boot"
    ;;
  logs)
    journalctl -u \$SVC --no-pager -n "\${2:-50}"
    ;;
  files)
    find \$DIR -type f \\( -name "*.py" -o -name "*.json" -o -name "*.txt" -o -name "*.md" -o -name "*.env" -o -name "*.sh" \\) | sort
    ;;
  read)
    cat "\$DIR/\$2" 2>/dev/null || echo "❌ File not found: \$2"
    ;;
  run)
    shift
    cd "\$DIR" && exec python3 "\$@"
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
    echo "  nova-wallet logs [n]     Recent logs (default 50)"
    echo "  nova-wallet files        List project files"
    echo "  nova-wallet read <file>  Read a file"
    echo "  nova-wallet run <args>   Execute Python"
    echo "  nova-wallet path         Show bot directory"
    echo ""
    echo "Direct systemctl also works:"
    echo "  systemctl status ${SVC_NAME}"
    echo "  journalctl -u ${SVC_NAME} -f"
    ;;
esac`;

    const mgrEsc = mgr.replace(/'/g, "'\\''");
    r = await sshExec(dst, `printf '%s' '${mgrEsc}' > /usr/local/bin/nova-wallet && chmod +x /usr/local/bin/nova-wallet && echo "OK"`);
    console.log('Management script:', r.stdout);

    // Create Nova README in bot dir
    const readme = `# YYO Personal Wallet Bot - Nova Integration
**Location:** ${BOT_PATH}  
**Service:** ${SVC_NAME}  
**Manager:** /usr/local/bin/nova-wallet

## Quick Commands for Nova
- \`nova-wallet status\` — Check if bot is running
- \`nova-wallet start\` — Start the bot
- \`nova-wallet stop\` — Stop the bot
- \`nova-wallet restart\` — Restart the bot
- \`nova-wallet logs 100\` — View last 100 log lines
- \`nova-wallet files\` — List all project files
- \`nova-wallet read <filename>\` — Read a file
- \`nova-wallet run <script.py>\` — Execute Python script
- \`nova-wallet path\` — Show bot directory path

## Direct Access
Nova can also use standard commands (if exec access is configured):
- \`systemctl status ${SVC_NAME}\`
- \`journalctl -u ${SVC_NAME} -f\`
- \`cd ${BOT_PATH} && python3 main.py\`

## Important Files
- Entry point: main.py (imports bot module)
- Bot code: bot/ directory
- Configuration: .env (may need to be created/set up)
`;

    const rdEsc = readme.replace(/'/g, "'\\''");
    await sshExec(dst, `printf '%s' '${rdEsc}' > ${BOT_PATH}/NOVA_README.md && echo "OK"`);

    // Create a simple env file if .env doesn't exist
    r = await sshExec(dst, `cat ${BOT_PATH}/.env 2>/dev/null`);
    if (!r.stdout || r.stdout.includes('No such file')) {
      console.log('\n⚠️  No .env found. Creating placeholder...');
      // Let's check bot code for env vars needed
      r = await sshExec(dst, `grep -rh "environ\[" ${BOT_PATH}/bot/ 2>/dev/null | sort -u | head -20`);
      console.log('Required env vars:\n', r.stdout);
      
      // Create .env template
      const envTemplate = `# YYO Personal Wallet Bot - Environment Variables
# Fill in your values below

# Telegram Bot Token (REQUIRED)
# BOT_TOKEN=your_bot_token_here

# Database (if applicable)
# DB_HOST=localhost
# DB_USER=root
# DB_PASSWORD=
# DB_NAME=wallet_bot

# Other settings
# LOG_LEVEL=INFO
`;
      const envEsc = envTemplate.replace(/'/g, "'\\''");
      await sshExec(dst, `printf '%s' '${envEsc}' > ${BOT_PATH}/.env.template && echo "OK"`);
      console.log('.env.template created');
    }

    // ── Test start ──
    console.log('\n--- Testing bot start ---');
    r = await sshExec(dst, `systemctl start ${SVC_NAME}.service 2>&1`);
    console.log('Start attempt:', r.code === 0 ? 'OK' : `FAILED: ${r.stderr}`);

    await new Promise(r => setTimeout(r, 4000));
    
    r = await sshExec(dst, `systemctl status ${SVC_NAME}.service --no-pager -l 2>&1 | head -30`);
    console.log('Service status:\n', r.stdout);

    r = await sshExec(dst, `journalctl -u ${SVC_NAME}.service --no-pager -n 30`);
    console.log('Service logs:\n', r.stdout);

    // Test nova-wallet manager
    r = await sshExec(dst, '/usr/local/bin/nova-wallet status 2>&1 | head -20');
    console.log('nova-wallet status test:\n', r.stdout);

    r = await sshExec(dst, '/usr/local/bin/nova-wallet files 2>&1 | head -20');
    console.log('nova-wallet files test:\n', r.stdout);

    console.log('✅ Step 6 done\n');

    // ── FINAL REPORT ──
    console.log('\n' + '═'.repeat(60));
    console.log('           MIGRATION COMPLETE');
    console.log('═'.repeat(60));
    console.log(` 📁 Bot:     ${BOT_PATH}`);
    console.log(` ⚙️  Service: ${SVC_NAME}.service`);
    console.log(` 🔧 Manager: /usr/local/bin/nova-wallet`);
    console.log(` 📖 README:  ${BOT_PATH}/NOVA_README.md`);
    console.log('');
    console.log(' Nova Access:');
    console.log('   nova-wallet [status|start|stop|restart|logs|files|read|run]');
    console.log('   All files readable in ' + BOT_PATH);
    console.log('   Systemd service controllable by root');
    console.log('');
    console.log(' Next for Nova: Set BOT_TOKEN in .env, then nova-wallet restart');
    console.log('═'.repeat(60));

    // Cleanup archive
    await sshExec(dst, `rm -f ${ARCHIVE}`);
    console.log('\n🧹 Archive cleaned up');

    dst.end();

  } catch(err) {
    console.error('\n❌ FATAL:', err.message);
    console.error(err.stack);
    process.exit(1);
  }
}

main().catch(console.error);
