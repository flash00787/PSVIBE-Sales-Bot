const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.error('Connected. Running manual deploy steps...');

  const steps = [
    'echo "=== STEP: Remove broken dir ==="',
    'rm -rf /root/Sales-Tele-Bot_refactored',
    'echo "✅ Removed"',
    '',
    'echo "=== STEP: Copy from staging ==="',
    'cp -a /root/staging/bot_src /root/Sales-Tele-Bot_refactored',
    'echo "✅ Copied"',
    '',
    'echo "=== STEP: Verify copied files ==="',
    'ls /root/Sales-Tele-Bot_refactored/main.py && ls /root/Sales-Tele-Bot_refactored/bot/app.py && ls /root/Sales-Tele-Bot_refactored/.env',
    'echo "✅ Core files present"',
    '',
    'echo "=== STEP: Ensure .env exists ==="',
    'if [ ! -f /root/Sales-Tele-Bot_refactored/.env ]; then cp /root/Sales-Tele-Bot/.env /root/Sales-Tele-Bot_refactored/.env && echo "✅ Copied .env from V1"; else echo "✅ .env already exists"; fi',
    '',
    'echo "=== STEP: Create logs directory ==="',
    'mkdir -p /root/Sales-Tele-Bot_refactored/logs',
    'echo "✅ logs/ created"',
    '',
    'echo "=== STEP: Set up venv (symlink from V1) ==="',
    'ln -sf /root/Sales-Tele-Bot/.venv /root/Sales-Tele-Bot_refactored/.venv',
    'ls /root/Sales-Tele-Bot_refactored/.venv/bin/python3',
    'echo "✅ venv linked"',
    '',
    'echo "=== STEP: Update service file ==="',
    'cat > /etc/systemd/system/psvibe-bot-refactored.service << \'SERVICEEOF\'',
    '[Unit]',
    'Description=PS Vibe Staff Bot V2 (Refactored)',
    'After=network.target',
    '',
    '[Service]',
    'Type=simple',
    'User=root',
    'WorkingDirectory=/root/Sales-Tele-Bot_refactored',
    'EnvironmentFile=/root/Sales-Tele-Bot_refactored/.env',
    'ExecStart=/root/Sales-Tele-Bot_refactored/.venv/bin/python3 main.py',
    'Restart=always',
    'RestartSec=3',
    'TimeoutStopSec=10',
    'KillSignal=SIGINT',
    'StandardOutput=append:/root/Sales-Tele-Bot_refactored/logs/bot.log',
    'StandardError=append:/root/Sales-Tele-Bot_refactored/logs/bot.log',
    '',
    '[Install]',
    'WantedBy=multi-user.target',
    'SERVICEEOF',
    'echo "✅ Service file updated"',
    '',
    'echo "=== STEP: Daemon reload ==="',
    'systemctl daemon-reload',
    'echo "✅ daemon-reload done"',
    '',
    'echo "=== STEP: Enable service ==="',
    'systemctl enable psvibe-bot-refactored.service',
    'echo "✅ enabled"',
    '',
    'echo "=== STEP: Start service ==="',
    'systemctl start psvibe-bot-refactored.service',
    'echo "✅ start command issued"',
    '',
    'echo "=== STEP: Wait and check ==="',
    'sleep 8',
    'systemctl is-active psvibe-bot-refactored.service',
    'echo "--- Status ---"',
    'systemctl status psvibe-bot-refactored.service 2>&1 | head -15',
    '',
    'echo "=== STEP: Log tail ==="',
    'tail -50 /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null || echo "(no logs yet)"',
    '',
    'echo "=== STEP: Import test ==="',
    'cd /root/Sales-Tele-Bot_refactored && /root/Sales-Tele-Bot_refactored/.venv/bin/python3 -c "from bot import *; print(\"✅ Import OK\")" 2>&1',
  ];

  const cmd = steps.join('\n');
  conn.exec(cmd, { pty: true }, (err, stream) => {
    if (err) { console.error('EXEC ERR:', err.message); conn.end(); process.exit(1); return; }
    let out = '';
    stream.on('data', d => { out += d; process.stderr.write(d); });
    stream.on('close', (code, signal) => {
      console.error('\n--- Finished with code:', code, '---');
      console.log('===MANUAL_DEPLOY_OUTPUT===');
      console.log(out);
      console.log('===END===');
      conn.end();
      process.exit(code || 0);
    });
  });
});

conn.on('error', e => { console.error('SSH error:', e.message); process.exit(1); });
conn.connect({
  host: '167.71.196.120',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
