const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

conn.on('ready', () => {
  conn.exec('pkill -f "uvicorn app:app" 2>/dev/null; sleep 1; cd /root/psvibe_api_server && SHEET_ID=1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA SERVICE_ACCOUNT_FILE=/root/psvibe_api_server/service_account.json nohup /root/psvibe_api_server/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 > /root/psvibe_api_server/server.log 2>&1 & echo "STARTED"', (err, stream) => {
    if (err) { console.error('ERROR:', err); conn.end(); return; }
    let data = '';
    stream.on('data', (chunk) => { data += chunk.toString(); });
    stream.stderr.on('data', (chunk) => { data += chunk.toString(); });
    stream.on('close', (code) => {
      console.log('EXIT:', code, '|', data.trim());
      conn.end();
    });
  });
});
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: key });
