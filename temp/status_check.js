const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

const commands = [
  "echo '=== PSVIBE SERVICES ==='",
  "for svc in psvibe-sale-bot psvibe_customer_bot psvibe-api psvibe-watchdog; do echo \"$svc: $(systemctl is-active \"$svc\" 2>&1)\"; done",
  "echo '=== CADDY ==='",
  "systemctl is-active caddy 2>&1; echo 'EXIT:'$?",
  "echo '=== N8N ==='",
  "systemctl is-active n8n 2>&1; echo 'EXIT:'$?",
  "echo '=== RECENT ERRORS ==='",
  "journalctl -u psvibe-sale-bot -u psvibe_customer_bot -u psvibe-api --since '1 hour ago' -n 50 --no-pager 2>&1 | grep -i -E 'error|traceback|failed|exception' | tail -30",
  "echo '=== DOCKER ==='",
  "docker ps --format 'table {{.Names}}\t{{.Status}}' 2>&1",
  "echo '=== DISK ==='",
  "df -h / | tail -1",
  "echo '=== MEMORY ==='",
  "free -h | grep Mem"
];

const fullCommand = commands.join('; ');

conn.on('ready', () => {
  conn.exec(fullCommand, (err, stream) => {
    if (err) {
      console.error('=== RESULT: ERROR: ' + err.message + ' ===');
      process.exit(1);
    }
    let output = '';
    stream.on('data', (data) => {
      output += data.toString();
    });
    stream.stderr.on('data', (data) => {
      output += '[STDERR] ' + data.toString();
    });
    stream.on('close', (code) => {
      fs.writeFileSync('/home/node/.openclaw/workspace/temp/status_check.txt', output);
      console.log(output);
      if (code === 0) {
        console.log('\n=== RESULT: OK ===');
      } else {
        console.log('\n=== RESULT: ERROR: SSH exit code ' + code + ' ===');
      }
      conn.end();
      process.exit(code);
    });
  });
});

conn.on('error', (err) => {
  console.error('=== RESULT: ERROR: ' + err.message + ' ===');
  process.exit(1);
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 10000
});
