const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const DIG_SCRIPT = `
#!/bin/bash
REPORT="/tmp/audit_dig_deeper.txt"
{
echo "=== DIG 1: Find correct MySQL password ==="
echo ""
# Check for MySQL password in configs
grep -r "MYSQL\|mysql.*password\|DB_PASS" /root/psvibe_api_server/*.py /root/psvibe_api_server/.env 2>/dev/null | grep -v ".pyc" | head -20
echo ""
echo "--- .env file ---"
cat /root/psvibe_api_server/.env 2>/dev/null || echo "(no .env)"
echo ""

echo "=== DIG 2: Find mysql password from docker inspect ==="
docker inspect psvibe-mysql 2>/dev/null | grep -i "MYSQL_ROOT_PASSWORD\|MYSQL_PASSWORD" | head -5
echo ""

echo "=== DIG 3: Try with no password or env var ==="
MYSQL_PWD=\$(docker exec psvibe-mysql printenv MYSQL_ROOT_PASSWORD 2>/dev/null || echo "")
echo "MYSQL_ROOT_PASSWORD env: '\$MYSQL_PWD'"
echo ""
echo "--- Try connecting without password ---"
docker exec psvibe-mysql mysql -u root -e "SELECT 1 AS test;" 2>&1
echo ""

echo "=== DIG 4: Find sheets_client.py ==="
find /root/psvibe-sales-bot -name "sheets_client.py" -type f 2>/dev/null
find /root/psvibe_api_server -name "sheets_client.py" -type f 2>/dev/null
echo ""

echo "=== DIG 5: Check save_receipt_json in ALL files ==="
grep -rn "save_receipt_json\|def.*receipt" /root/psvibe_api_server/*.py /root/psvibe-sales-bot/bot/*.py 2>/dev/null | grep -v ".pyc" | grep -v ".bak" | head -20
echo ""

echo "=== DIG 6: Check app.py for MySQL/receipt patterns ==="
grep -n "receipt\|mysql\|INSERT" /root/psvibe_api_server/app.py 2>/dev/null | head -20
echo ""

echo "=== DIG 7: Check api_client.py FULL retry/backoff implementation ==="
grep -n -i "retr\|backoff\|sleep\b\|DEFAULT_MAX\|for.*range\|while.*attempt\|except.*URLError\|except.*HTTPError" /root/psvibe-sales-bot/bot/api_client.py 2>/dev/null | head -30
echo ""
echo "--- _api_call full function ---"
awk '/^def _api_call/,/^def [^_]/' /root/psvibe-sales-bot/bot/api_client.py 2>/dev/null | head -80
echo ""

echo "=== DIG 8: Check api_server app.py for any routes ==="
grep -n "@app\.\|@router\|def.*endpoint\|def.*route" /root/psvibe_api_server/app.py 2>/dev/null | head -30
echo ""

echo "=== DIG 9: get_console_booking_rows in all files ==="
grep -rn "def get_console_booking_rows\|get_console_booking" /root/psvibe-sales-bot/ /root/psvibe_api_server/ 2>/dev/null | grep -v ".pyc" | head -10
echo ""

echo "=== DIG 10: Check what sheets_client files exist anywhere ==="
find /root -name "*sheets_client*" -type f 2>/dev/null | head -10
echo ""

echo "=== DIG 11: API health endpoint ==="
curl -s http://localhost:8000/api/health 2>&1 || echo "curl failed"
echo ""
curl -s http://localhost:8000/health 2>&1 || echo "curl failed"
echo ""

echo "=== DIG 12: git diff for uncommitted changes (psvibe_api_server) ==="
cd /root/psvibe_api_server && git diff --stat 2>/dev/null
echo ""
cd /root/psvibe_api_server && git diff app.py 2>/dev/null | head -60
echo ""

} > "\$REPORT" 2>&1
cat "\$REPORT"
`;

const conn = new Client();

conn.on('ready', () => {
  console.log('[SSH] Deep dig running...\n');
  conn.exec(DIG_SCRIPT, { pty: false }, (err, stream) => {
    if (err) throw err;
    let stdout = '';
    stream.on('data', (data) => { stdout += data.toString(); process.stdout.write(data.toString()); });
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
