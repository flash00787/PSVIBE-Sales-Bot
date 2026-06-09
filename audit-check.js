const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();

const commands = {
  services: 'systemctl is-active psvibe-sale-bot psvibe_customer_bot psvibe-api 2>&1',
  main_py_count: 'ps aux | grep "[m]ain.py" | wc -l',
  customer_bot_count: 'ps aux | grep "customer_bot" | grep -v grep | wc -l',
  api_response: 'curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ 2>/dev/null; echo ""',
  file_count: 'find /root/psvibe-sales-bot -name "*.py" -type f 2>/dev/null | wc -l',
  bot_started: 'journalctl -u psvibe-sale-bot --since "15 min ago" --no-pager 2>/dev/null | grep "Application started" | tail -1',
  recent_errors: 'journalctl -u psvibe-sale-bot --since "5 min ago" --no-pager 2>/dev/null | grep -i "error\\|CRITICAL" | grep -v "Conflict\\|429\\|500" | tail -3',
  docker_ps: 'docker ps --filter "status=running" --format "{{.Names}}" 2>/dev/null',
  disk: 'df -h / | tail -1',
};

conn.on('ready', () => {
  const results = {};
  const keys = Object.keys(commands);
  let completed = 0;

  keys.forEach((key) => {
    conn.exec(commands[key], (err, stream) => {
      if (err) {
        results[key] = `ERROR: ${err.message}`;
        completed++;
        if (completed === keys.length) finish(results);
        return;
      }
      let output = '';
      stream.on('data', (data) => { output += data.toString(); });
      stream.stderr.on('data', (data) => { output += data.toString(); });
      stream.on('close', () => {
        results[key] = output.trim();
        completed++;
        if (completed === keys.length) finish(results);
      });
    });
  });
});

function finish(results) {
  console.log(JSON.stringify(results, null, 2));
  conn.end();
}

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync(path.join(__dirname, '.ssh', 'id_rsa')),
  readyTimeout: 10000,
});
