const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const DIG4_SCRIPT = `
#!/bin/bash
REPORT="/tmp/audit_dig4.txt"
{
echo "=== P2: staff_records_bak structure ==="
docker exec -e MYSQL_PWD='PsVibe@MySQL2024!' psvibe-mysql mysql -u root -e "SHOW CREATE TABLE psvibe_api.staff_records_bak\\G" 2>&1
echo ""
echo "=== P2: staff_records_bak row count ==="
docker exec -e MYSQL_PWD='PsVibe@MySQL2024!' psvibe-mysql mysql -u root -e "SELECT COUNT(*) AS row_count FROM psvibe_api.staff_records_bak;" 2>&1
echo ""

echo "=== P2: staff_records_bak indexes ==="
docker exec -e MYSQL_PWD='PsVibe@MySQL2024!' psvibe-mysql mysql -u root -e "SHOW INDEX FROM psvibe_api.staff_records_bak;" 2>&1
echo ""

echo "=== Check all tables in psvibe_api ==="
docker exec -e MYSQL_PWD='PsVibe@MySQL2024!' psvibe-mysql mysql -u root -e "SHOW TABLES FROM psvibe_api;" 2>&1
echo ""

echo "=== Check if receipts table exists ==="
docker exec -e MYSQL_PWD='PsVibe@MySQL2024!' psvibe-mysql mysql -u root -e "SELECT COUNT(*) FROM psvibe_api.receipts;" 2>&1
echo ""

echo "=== P4: POST endpoints in app.py ==="
grep -n "@app.post" /root/psvibe_api_server/app.py 2>/dev/null | head -20
echo ""

echo "=== P5: Verify retry with simple grep ==="
grep "DEFAULT_MAX_RETRIES\|DEFAULT_RETRY_BASE_DELAY\|for attempt\|exponential" /root/psvibe-sales-bot/bot/api_client.py
echo ""

echo "=== Check if api_client has _api_call function ==="
python3 -c "
import ast, sys
with open('/root/psvibe-sales-bot/bot/api_client.py') as f:
    t = ast.parse(f.read())
imports = [n for n in ast.walk(t) if isinstance(n, ast.Import) or isinstance(n, ast.ImportFrom)]
funcs = [n.name for n in ast.walk(t) if isinstance(n, ast.FunctionDef)]
print('Functions:', funcs)
" 2>&1
echo ""

echo "=== Check for any receipt/save functions in entire project ==="
grep -rn "def.*receipt\|save_receipt\|receipt.*insert\|INSERT.*receipt" /root/psvibe_api_server/ /root/psvibe-sales-bot/ 2>/dev/null | grep -v ".pyc" | grep -v ".bak" | head -10
echo ""

} > "\$REPORT" 2>&1
cat "\$REPORT"
`;

const conn = new Client();

conn.on('ready', () => {
  console.log('[SSH] Dig 4 running...\n');
  conn.exec(DIG4_SCRIPT, { pty: false }, (err, stream) => {
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
