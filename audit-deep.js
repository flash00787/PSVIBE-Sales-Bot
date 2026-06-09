const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

const commands = [
  { label: 'status', cmd: 'systemctl status psvibe-sale-bot --no-pager -l 2>&1 | head -30' },
  { label: 'ps', cmd: 'ps aux | grep "[m]ain.py"' },
  { label: 'journal', cmd: 'journalctl -u psvibe-sale-bot --since "2 hours ago" --no-pager 2>/dev/null | grep -i "started\\|error\\|CRITICAL" | grep -v "Conflict\\|429\\|500" | tail -10' },
  { label: 'root', cmd: 'curl -s http://localhost:8000/ 2>/dev/null | head -c 500' },
  { label: 'health', cmd: 'curl -s http://localhost:8000/health 2>/dev/null | head -c 300' },
  { label: 'services', cmd: 'systemctl list-units --type=service | grep psvibe' },
];

conn.on('ready', () => {
  const results = {};
  let done = 0;

  commands.forEach(({ label, cmd }) => {
    conn.exec(cmd, (err, stream) => {
      if (err) { results[label] = `ERR: ${err.message}`; done++; checkFinish(); return; }
      let out = '';
      stream.on('data', (d) => out += d.toString());
      stream.stderr.on('data', (d) => out += d.toString());
      stream.on('close', () => { results[label] = out.trim(); done++; checkFinish(); });
    });
  });

  function checkFinish() {
    if (done === commands.length) {
      Object.entries(results).forEach(([k, v]) => console.log(`--- ${k} ---\n${v}\n`));
      conn.end();
    }
  }
});

conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'), readyTimeout: 10000 });
