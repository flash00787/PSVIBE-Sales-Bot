const { Client } = require('ssh2');
const fs = require('fs');

const commands = [
  'echo "=== MYSQL_TABLES_psvibe_api ==="',
  'docker exec psvibe-mysql mysql -u root -p"PsVibe@MySQL2024!" -e "USE psvibe_api; SHOW TABLES;" 2>&1',
  'echo "=== MYSQL_SCHEMAS ==="',
  'docker exec psvibe-mysql mysql -u root -p"PsVibe@MySQL2024!" -e "SELECT table_name, column_name, column_type, is_nullable, column_key, extra FROM information_schema.columns WHERE table_schema = \"psvibe_api\" ORDER BY table_name, ordinal_position;" 2>&1',
  'echo "=== MYSQL_DATA ==="',
  'docker exec psvibe-mysql mysql -u root -p"PsVibe@MySQL2024!" -e "USE psvibe_api; SELECT * FROM sync_status; SELECT * FROM console_status;" 2>&1',
  'echo "=== API_SERVER_DIR ==="',
  'ls -la /root/psvibe_api_server/ 2>&1',
  'echo "=== API_SERVER_FILES ==="',
  'find /root/psvibe_api_server -type f -name "*.py" 2>/dev/null | sort',
  'echo "=== API_APP_PY ==="',
  'cat /root/psvibe_api_server/app.py 2>/dev/null || cat /root/psvibe_api_server/main.py 2>/dev/null || echo "NO_API_APP"',
  'echo "=== API_LOGS ==="',
  'docker logs --tail 30 $(docker ps -q --filter name=psvibe-mysql) 2>&1',
  'echo "=== API_SERVER_PROCESS ==="',
  'ps aux | grep "psvibe_api_server" | grep -v grep 2>&1',
  'echo "=== N8N_SYNC ==="',
  'curl -s http://localhost:5678/healthz 2>&1 || echo "N8N not responding"',
  'echo "=== API_PORT_8000 ==="',
  'curl -s http://localhost:8000/ 2>&1 | head -20 || echo "NO_RESPONSE"',
  'echo "=== N8N_WEBHOOKS ==="',
  'curl -s -X GET "http://localhost:5678/webhook/" 2>&1 | head -5 || echo "N8N no response"',
];

const conn = new Client();
let output = '';
let cmdIdx = 0;

conn.on('ready', () => {
  runNext();
});

function runNext() {
  if (cmdIdx >= commands.length) {
    conn.end();
    setTimeout(() => { console.log(output); process.exit(0); }, 500);
    return;
  }
  conn.exec(commands[cmdIdx], (err, stream) => {
    if (err) { output += `\n[ERR]: ${err.message}\n`; cmdIdx++; runNext(); return; }
    let data = '';
    stream.on('data', d => data += d.toString());
    stream.stderr.on('data', d => data += '[STDERR] ' + d.toString());
    stream.on('close', () => { output += data + '\n---\n'; cmdIdx++; runNext(); });
  });
}
conn.on('error', e => { console.log('ERR:', e.message); process.exit(1); });
conn.connect({host:'5.223.81.16',username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),readyTimeout:15000});
setTimeout(() => { try { conn.end(); } catch(e) {} console.log(output); process.exit(0); }, 60000);
