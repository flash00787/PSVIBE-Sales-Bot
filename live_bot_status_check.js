const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('--- Connected to bot-server-01 VPS (167.71.196.120) via SSH ---');

  const commands = [
    { name: 'PM2 Processes Status', cmd: 'pm2 list || pm2 status' },
    { name: 'Docker Containers Status', cmd: 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"' },
    { name: 'Running Python Bots Processes', cmd: 'ps aux | grep -i -E "python.*bot|main\\.py|customer_bot\\.py" | grep -v grep' },
    { name: 'Systemd Services for PS Vibe & Wallet', cmd: 'systemctl list-units --type=service | grep -i -E "psvibe|wallet|bot|agri"' },
    { name: 'Files in /root', cmd: 'ls -F /root' },
    { name: 'Sales-Tele-Bot Git Status & Last Log', cmd: 'cd /root/Sales-Tele-Bot && git status -s && git log -n 3 --oneline || echo "Not a git repo or directory missing"' },
    { name: 'Personal-Wallet-Tele-Bot-2 Git Status & Last Log', cmd: 'cd /root/Personal-Wallet-Tele-Bot-2 && git status -s && git log -n 3 --oneline || echo "Not a git repo or directory missing"' },
    { name: 'PS Vibe Customer Service Log (Last 15 lines)', cmd: 'journalctl -u psvibe-customer -n 15 --no-pager || echo "No service logs available"' },
    { name: 'PS Vibe Staff Service Log (Last 15 lines)', cmd: 'journalctl -u psvibe-staff -n 15 --no-pager || echo "No service logs available"' },
    { name: 'Wallet Bot Service Log (Last 15 lines)', cmd: 'journalctl -u personal-wallet -n 15 --no-pager || echo "No service logs available"' },
  ];

  let idx = 0;

  function runNext() {
    if (idx >= commands.length) {
      conn.end();
      return;
    }
    const item = commands[idx++];
    console.log(`\n==================================================`);
    console.log(`🔍 STATUS CHECK: ${item.name}`);
    console.log(`==================================================`);
    conn.exec(item.cmd, { pty: false }, (err, stream) => {
      if (err) {
        console.log(`EXEC ERROR:`, err);
        runNext();
        return;
      }
      let output = '';
      stream.on('data', (data) => { output += data.toString(); });
      stream.stderr.on('data', (data) => { output += data.toString(); });
      stream.on('close', (code) => {
        console.log(output.trim() || '(No output/No process running)');
        runNext();
      });
    });
  }

  runNext();
});

conn.on('error', (err) => {
  console.error('SSH CONNECTION ERROR:', err);
  process.exit(1);
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
