const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const AUDIT_SCRIPT = `
#!/bin/bash
REPORT="/tmp/audit_all_fixes.txt"
{
echo "========================================================================"
echo "   PS VIBE FULL AUDIT REPORT - $(date '+%Y-%m-%d %H:%M:%S UTC')"
echo "   All fixes deployed 2026-05-29"
echo "========================================================================"
echo ""

# ─── P0: Services Health ───
echo "=== P0: SYSTEMD SERVICE STATUS ==="
echo ""
for svc in psvibe-sale-bot psvibe-api psvibe_customer_bot; do
  status=\$(systemctl is-active \$svc 2>&1)
  printf "%-35s ACTIVE=%s\\n" "\$svc.service" "\$status"
done
echo ""
for svc in psvibe-sale-bot psvibe-api psvibe_customer_bot; do
  echo "--- \$svc (last 3 log lines) ---"
  journalctl -u \$svc.service --no-pager -n 3 2>&1 | tail -3
  echo ""
done

# ─── P0: Git Status ───
echo "=== P0: GIT STATUS ==="
echo ""
echo "[psvibe-sales-bot]"
cd /root/psvibe-sales-bot && echo "Last commit:" && git log --oneline -3 2>&1
echo ""
cd /root/psvibe-sales-bot && echo "Uncommitted changes:" && git status --short 2>&1 || echo "(clean)"
echo ""

echo "[psvibe_api_server]"
cd /root/psvibe_api_server 2>/dev/null && echo "Last commit:" && git log --oneline -3 2>&1 || echo "(no git repo)"
echo ""
cd /root/psvibe_api_server 2>/dev/null && echo "Uncommitted:" && git status --short 2>&1 || echo "(no git repo)"
echo ""

# ─── P0: Tests ───
echo "=== P0: TEST SUITE ==="
echo ""
cd /root/psvibe-sales-bot && python3 -m pytest tests/ -q 2>&1
echo ""

# ─── P1: save_receipt_json → MySQL INSERT ───
echo "==========================================="
echo "   P1: save_receipt_json → MySQL INSERT"
echo "==========================================="
echo ""
echo "--- Checking save_receipt_json function ---"
grep -n "def save_receipt_json" /root/psvibe_api_server/app.py 2>&1 || echo "❌ FUNCTION NOT FOUND"
echo ""
echo "--- Checking mysql_execute / INSERT INTO receipts ---"
grep -n "mysql_execute\|INSERT.*receipts" /root/psvibe_api_server/app.py 2>&1 | head -10 || echo "❌ NO MYSQL REFERENCES FOUND"
echo ""
echo "--- Checking receipt count in MySQL ---"
docker exec psvibe-mysql mysql -u root -pPsVibe@2026_Rotated! -e "SELECT COUNT(*) AS receipt_count FROM psvibe_api.receipts;" 2>&1 || echo "❌ QUERY FAILED"
echo ""

# ─── P2: staff_records_bak UNIQUE INDEX ───
echo "==========================================="
echo "   P2: staff_records_bak UNIQUE INDEX"
echo "==========================================="
echo ""
echo "--- Table structure ---"
docker exec psvibe-mysql mysql -u root -pPsVibe@2026_Rotated! -e "SHOW CREATE TABLE psvibe_api.staff_records_bak\\G" 2>&1 | grep -i "unique\|index\|KEY\|Create Table"
echo ""
echo "--- Row count ---"
docker exec psvibe-mysql mysql -u root -pPsVibe@2026_Rotated! -e "SELECT COUNT(*) AS row_count FROM psvibe_api.staff_records_bak;" 2>&1 || echo "❌ QUERY FAILED"
echo ""

# ─── P3: get_console_booking_rows() ───
echo "==========================================="
echo "   P3: get_console_booking_rows()"
echo "==========================================="
echo ""
echo "--- Checking function in sheets_client.py ---"
grep -n "def get_console_booking_rows" /root/psvibe-sales-bot/bot/utils/sheets_client.py 2>&1 || echo "❌ FUNCTION NOT FOUND"
echo ""
echo "--- Surrounding context ---"
grep -n -A 15 "def get_console_booking_rows" /root/psvibe-sales-bot/bot/utils/sheets_client.py 2>&1 || echo "❌ NOT FOUND"
echo ""

# ─── P4: API endpoints + wrappers + handlers ───
echo "==========================================="
echo "   P4: API ENDPOINTS + WRAPPERS + HANDLERS"
echo "==========================================="
echo ""
echo "--- API endpoints (opex/salary_advance/sales/stock/register/topup) ---"
grep -n "POST\|@router\|@app" /root/psvibe_api_server/app.py 2>&1 | grep -i "opex\|salary_advance\|sales_record\|stock_out\|stock_in\|register_member\|topup" | head -15 || echo "❌ NONE FOUND"
echo ""
echo "--- api_client wrapper functions ---"
grep "def api_add_" /root/psvibe-sales-bot/bot/api_client.py 2>&1 | head -20 || echo "❌ NONE FOUND"
echo ""
echo "--- Handler API call counts ---"
count=\$(grep -rn "api_add_" /root/psvibe-sales-bot/bot/handlers/ 2>&1 | wc -l)
echo "Total api_add_ calls in handlers: \$count"
echo ""
echo "--- Sample handler calls ---"
grep -rn "api_add_" /root/psvibe-sales-bot/bot/handlers/ 2>&1 | head -10 || echo "❌ NONE FOUND"
echo ""

# ─── P5: Retry/backoff on _api_call ───
echo "==========================================="
echo "   P5: RETRY/BACKOFF ON _api_call"
echo "==========================================="
echo ""
echo "--- _api_call function header ---"
grep -A 15 "def _api_call" /root/psvibe-sales-bot/bot/api_client.py 2>&1 | head -20 || echo "❌ NOT FOUND"
echo ""
echo "--- Retry pattern counts ---"
echo -n "retry: "; grep -c "retry\|backoff\|max_retries\|sleep" /root/psvibe-sales-bot/bot/api_client.py 2>&1 || echo "0"
echo -n "Retry: "; grep -c "Retry\|Backoff\|Max_retries\|Sleep" /root/psvibe-sales-bot/bot/api_client.py 2>&1 || echo "0"
echo ""

# ─── API Health Endpoint ───
echo "==========================================="
echo "   BONUS: API HEALTH ENDPOINT"
echo "==========================================="
echo ""
echo "--- Health check route ---"
grep -B 2 -A 10 "def health\|/api/health\|async def health\|/health" /root/psvibe_api_server/app.py 2>&1 | head -20 || echo "❌ NOT FOUND"
echo ""

# ─── Import/Circular Dependency Check ───
echo "==========================================="
echo "   BONUS: IMPORT & DEPENDENCY CHECK"
echo "==========================================="
echo ""
echo "--- api_client imports (check for urllib3 retry) ---"
head -30 /root/psvibe-sales-bot/bot/api_client.py 2>&1
echo ""
echo "--- Checking for requests Session with retry ---"
grep -n "Session\|HTTPAdapter\|Retry\|mount\|adapter" /root/psvibe-sales-bot/bot/api_client.py 2>&1 || echo "(none)"
echo ""

# ─── Docker health ───
echo "=== DOCKER CONTAINERS ==="
echo ""
docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}" 2>&1 | grep -i mysql || echo "❌ psvibe-mysql not running"
echo ""

# ─── Disk & Memory ───
echo "=== SYSTEM RESOURCES ==="
echo ""
echo "Disk:"
df -h / 2>&1 | tail -1
echo ""
echo "Memory:"
free -h 2>&1 | head -2
echo ""

# ─── Wrap-up timestamp ───
echo ""
echo "========================================================================"
echo "AUDIT COMPLETE - $(date '+%Y-%m-%d %H:%M:%S UTC')"
echo "========================================================================"
} > "\$REPORT" 2>&1
cat "\$REPORT"
`;

const conn = new Client();

conn.on('ready', () => {
  console.log('[SSH] Connected. Running full audit...\n');
  conn.exec(AUDIT_SCRIPT, { pty: false }, (err, stream) => {
    if (err) throw err;
    let stdout = '';
    let stderr = '';
    stream.on('data', (data) => { stdout += data.toString(); process.stdout.write(data.toString()); });
    stream.stderr.on('data', (data) => { stderr += data.toString(); process.stderr.write(data.toString()); });
    stream.on('close', (code) => {
      if (stderr && !stderr.includes('Warning') && !stderr.includes('mariadb') && !stderr.includes('Pseudo-terminal')) {
        // Only show stderr that isn't just MySQL warnings
      }
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
