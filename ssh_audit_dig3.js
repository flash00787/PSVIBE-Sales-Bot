const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const DIG3_SCRIPT = `
#!/bin/bash
REPORT="/tmp/audit_dig3.txt"
{
echo "=== app.py: first 50 lines ==="
head -50 /root/psvibe_api_server/app.py
echo ""
echo "=== app.py: line count ==="
wc -l /root/psvibe_api_server/app.py
echo ""

echo "=== app.py: grep for @app (any pattern) ==="
grep -n "@app" /root/psvibe_api_server/app.py 2>/dev/null | head -30
echo ""

echo "=== app.py: grep for def (functions) ==="
grep -n "^def \|^async def " /root/psvibe_api_server/app.py 2>/dev/null | head -40
echo ""

echo "=== api_client.py: line count ==="
wc -l /root/psvibe-sales-bot/bot/api_client.py
echo ""

echo "=== api_client.py: grep retry/backoff/attempt ==="
grep -n -i "retr\|backoff\|attempt\|delay\|sleep" /root/psvibe-sales-bot/bot/api_client.py 2>/dev/null
echo ""

echo "=== sheets_client.py: line count ==="
wc -l /root/psvibe_api_server/sheets_client.py
echo ""

echo "=== sheets_client.py: grep console ==="
grep -n -i "console" /root/psvibe_api_server/sheets_client.py 2>/dev/null | head -20
echo ""

echo "=== sheets_client.py: function defs ==="
grep -n "^def " /root/psvibe_api_server/sheets_client.py 2>/dev/null | head -20
echo ""

echo "=== mysql_db.py: exists? content? ==="
wc -l /root/psvibe_api_server/mysql_db.py 2>/dev/null || echo "(file not found)"
grep -n "^def " /root/psvibe_api_server/mysql_db.py 2>/dev/null | head -20 || echo "(no functions)"
echo ""

echo "=== MySQL: try with docker exec -e ==="
docker exec -e MYSQL_PWD='PsVibe@MySQL2024!' psvibe-mysql mysql -u root -e "SELECT 1 AS test_connection;" 2>&1
echo ""

echo "=== MySQL: try with direct host connection ==="
mysql -h 127.0.0.1 -P 3306 -u root -p'PsVibe@MySQL2024!' -e "SELECT 1;" 2>&1
echo ""

echo "=== MySQL: try with no root password (socket) ==="
docker exec psvibe-mysql mysql -e "SELECT 1;" 2>&1
echo ""

echo "=== MySQL: check docker compose/run config ==="
docker inspect psvibe-mysql --format '{{json .Config.Env}}' 2>/dev/null | python3 -m json.tool 2>/dev/null || docker inspect psvibe-mysql --format '{{json .Config.Env}}'
echo ""

} > "\$REPORT" 2>&1
cat "\$REPORT"
`;

const conn = new Client();

conn.on('ready', () => {
  console.log('[SSH] Dig 3 running...\n');
  conn.exec(DIG3_SCRIPT, { pty: false }, (err, stream) => {
    if (err) throw err;
    stream.on('data', (data) => { process.stdout.write(data.toString()); });
    stream.stderr.on('data', (data) => { process.stderr.write(data.toString()); });
    stream.on('close', (code) => {
      conn.end();
      process.exit(code || 0);
    });
  });
});

conn.on('error', (err) => {
  console.error('SSH error:', err.message);
  process.exit(1);
});

conn.connect({
  host: HOST,
  port: 22,
  username: USER,
  privateKey: fs.readFileSync(KEY_PATH)
});
