const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const PRIVATE_KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
const TARGET = '/root/Sales-Tele-Bot_refactored';
const VENV = '/root/venv';

const SERVICE = `[Unit]
Description=PS VIBE Telegram Bot (V2 Refactored)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${TARGET}
EnvironmentFile=${TARGET}/.env
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONPATH=${TARGET}
ExecStart=${VENV}/bin/python3 ${TARGET}/main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=psvibe-bot

[Install]
WantedBy=multi-user.target
`;

async function main() {
  const conn = new Client();
  await new Promise((res, rej) => {
    conn.on('ready', res);
    conn.on('error', rej);
    conn.connect({ host: HOST, port: 22, username: 'root', privateKey: PRIVATE_KEY, readyTimeout: 30000 });
  });
  console.log('SSH connected');

  const execOk = (cmd) => new Promise((res) => {
    console.log(`\n>>> ${cmd.slice(0, 150)}`);
    conn.exec(cmd, (err, stream) => {
      if (err) { console.error('exec err:', err); res(''); return; }
      let out = '';
      stream.on('data', d => { out += d.toString(); process.stdout.write(d.toString()); });
      stream.stderr.on('data', d => { process.stderr.write('E:'+d); out += d.toString(); });
      stream.on('close', () => res(out));
    });
  });

  // Step 1: Write service file
  console.log('Writing service file...');
  await new Promise((res, rej) => {
    conn.sftp((err, sftp) => {
      if (err) { rej(err); return; }
      const w = sftp.createWriteStream('/etc/systemd/system/psvibe-bot.service');
      w.on('close', () => { console.log('Service file written'); res(); });
      w.on('error', rej);
      w.end(SERVICE);
    });
  });

  // Step 2: Verify service file
  await execOk('cat /etc/systemd/system/psvibe-bot.service');

  // Step 3: Daemon reload
  await execOk('systemctl daemon-reload && echo "daemon-reload OK"');

  // Step 4: Stop any existing bot processes
  await execOk('pkill -f "python3 main.py" 2>/dev/null; echo "killed old processes (if any)"');

  // Step 5: Remove old lock file
  await execOk('rm -f /tmp/ps_vibe_bot.lock && echo "lock removed"');

  // Step 6: Start the service
  await execOk('systemctl start psvibe-bot.service && echo "service started"');

  // Step 7: Wait 3s then check status
  await new Promise(r => setTimeout(r, 3000));
  await execOk('systemctl status psvibe-bot.service --no-pager');

  // Step 8: Check logs
  await execOk('journalctl -u psvibe-bot.service --no-pager -n 30');

  // Step 9: Enable on boot
  await execOk('systemctl enable psvibe-bot.service && echo "enabled on boot"');

  conn.end();
  console.log('\n=== Deployment complete ===');
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
