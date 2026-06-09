const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const DIG2_SCRIPT = `
#!/bin/bash
REPORT="/tmp/audit_dig2.txt"
{
echo "=== P1: MySQL receipt check with correct password ==="
MYSQL_PWD='PsVibe@MySQL2024!' docker exec psvibe-mysql mysql -u root -e "SELECT COUNT(*) AS receipt_count FROM psvibe_api.receipts;" 2>&1
echo ""
echo "--- Check if receipts table exists ---"
MYSQL_PWD='PsVibe@MySQL2024!' docker exec psvibe-mysql mysql -u root -e "SHOW TABLES FROM psvibe_api LIKE '%receipt%';" 2>&1
echo ""

echo "=== P2: staff_records_bak UNIQUE INDEX ==="
MYSQL_PWD='PsVibe@MySQL2024!' docker exec psvibe-mysql mysql -u root -e "SHOW CREATE TABLE psvibe_api.staff_records_bak\\G" 2>&1
echo ""
MYSQL_PWD='PsVibe@MySQL2024!' docker exec psvibe-mysql mysql -u root -e "SELECT COUNT(*) FROM psvibe_api.staff_records_bak;" 2>&1
echo ""

echo "=== Check save_receipt in mysql_db.py (new file) ==="
grep -n "receipt\|def save" /root/psvibe_api_server/mysql_db.py 2>/dev/null | head -20
echo ""

echo "=== Check for receipt in app.py uncommitted ==="
grep -n "receipt\|INSERT INTO" /root/psvibe_api_server/app.py 2>/dev/null | head -20
echo ""

echo "=== Check all app.py routes (FastAPI decorators) ==="
grep -n "@app\.\(get\|post\|put\|delete\|patch\)" /root/psvibe_api_server/app.py 2>/dev/null | head -30
echo ""

echo "=== Check sheets_client.py for get_console_booking ==="
grep -n "console_booking\|def get_console" /root/psvibe_api_server/sheets_client.py 2>/dev/null | head -10
echo ""

echo "=== Check retry full implementation in api_client ==="
grep -n "DEFAULT_RETRY_BASE_DELAY\|DEFAULT_MAX_RETRIES\|for attempt\|delay.*backoff\|exponential" /root/psvibe-sales-bot/bot/api_client.py 2>/dev/null
echo ""

echo "=== Verify API health endpoint works ==="
curl -s http://localhost:8000/api/health 2>&1
echo ""

echo "=== Check psvibe_api database tables ==="
MYSQL_PWD='PsVibe@MySQL2024!' docker exec psvibe-mysql mysql -u root -e "SHOW TABLES FROM psvibe_api;" 2>&1
echo ""

echo "=== Check all receipt-related files ==="
find /root -name "*receipt*" -type f 2>/dev/null | head -10
echo ""

} > "\$REPORT" 2>&1
cat "\$REPORT"
`;

const conn = new Client();

conn.on('ready', () => {
  console.log('[SSH] Dig 2 running...\n');
  conn.exec(DIG2_SCRIPT, { pty: false }, (err, stream) => {
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
