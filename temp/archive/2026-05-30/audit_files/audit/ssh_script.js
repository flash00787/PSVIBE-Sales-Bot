const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

function sshExec(commands, timeout = 60000) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let result = '';
    let done = false;
    
    const timer = setTimeout(() => {
      if (!done) {
        done = true;
        conn.end();
        resolve(result + '\n[TIMEOUT]');
      }
    }, timeout);

    conn.on('ready', () => {
      conn.exec(commands, (err, stream) => {
        if (err) { clearTimeout(timer); conn.end(); reject(err); return; }
        stream.on('data', (data) => { result += data.toString(); });
        stream.stderr.on('data', (data) => { result += data.toString(); });
        stream.on('close', () => {
          clearTimeout(timer);
          if (!done) { done = true; conn.end(); resolve(result); }
        });
      });
    });
    conn.on('error', (err) => { clearTimeout(timer); if (!done) { done = true; reject(err); } });
    conn.connect({ host: HOST, port: 22, username: USER, privateKey: KEY });
  });
}

async function main() {
  // Step 1: Read api_client.py
  console.log('=== READING api_client.py ===');
  let apiClient = await sshExec('cat /root/psvibe-sale-bot/bot/api_client.py', 30000);
  fs.writeFileSync('/home/node/.openclaw/workspace/audit/api_client_raw.py', apiClient);
  console.log('api_client.py lines:', apiClient.split('\n').length);
  
  // Step 2: Read __init__.py for sheet references
  console.log('=== READING __init__.py ===');
  let initPy = await sshExec('cat /root/psvibe-sale-bot/bot/__init__.py', 60000);
  fs.writeFileSync('/home/node/.openclaw/workspace/audit/init_raw.py', initPy);
  console.log('__init__.py lines:', initPy.split('\n').length);
  
  // Step 3: Get env file for sheet ID
  console.log('=== READING .env ===');
  let envFile = await sshExec('cat /root/psvibe-sale-bot/.env 2>/dev/null || echo "NO_ENV_FILE"');
  fs.writeFileSync('/home/node/.openclaw/workspace/audit/env_file.txt', envFile);
  
  // Step 4: Test API endpoints with curl
  console.log('=== TESTING API ENDPOINTS ===');
  let apiTests = await sshExec(`
echo "---HEALTH---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_MEMBERS---"
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/fetch_members 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_MEMBERS_GET---"
curl -s -o /dev/null -w "%{http_code}" -X GET http://localhost:8000/api/fetch_members 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_MEMBER_DATA---"
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/fetch_member_data/1 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_STAFF---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/fetch_staff 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_GAMES---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/fetch_games 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_BASE_RATE---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/fetch_base_rate 2>/dev/null || echo "FAIL"
echo ""
echo "---NEXT_VOUCHER---"
curl -s -o /dev/null -w "%{http_code}" -X GET http://localhost:8000/api/next_voucher 2>/dev/null || echo "FAIL"
echo ""
echo "---CREATE_BOOKING---"
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/create_booking 2>/dev/null || echo "FAIL"
echo ""
echo "---SAVE_ATTENDANCE---"
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/save_attendance 2>/dev/null || echo "FAIL"
echo ""
echo "---SAVE_RECEIPT_JSON---"
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/save_receipt_json 2>/dev/null || echo "FAIL"
echo ""
echo "---SHEETS_CONFIG---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/sheets/config 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_CONSOLE_STATUS---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/fetch_console_status 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_FOOD_PRICES---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/fetch_food_prices 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_CONSOLE_MULTIPLIER---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/fetch_console_multiplier/1 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_RANK_THRESHOLDS---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/fetch_rank_thresholds 2>/dev/null || echo "FAIL"
echo ""
echo "---BUILD_MEMBER_RATE_DICT---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/build_member_rate_dict 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_ATTENDANCE---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/fetch_attendance/2024-01 2>/dev/null || echo "FAIL"
echo ""
echo "---NEXT_MEMBER_ID---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/next_member_id 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_GAME_LIBRARY---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/fetch_game_library 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_MEMBER_EFFECTIVE_RATE---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/fetch_member_effective_rate/1 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_ALLTIME_EFFECTIVE_RATE---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/fetch_alltime_effective_rate 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_PROMOTIONS_CACHED---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/fetch_promotions_cached 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_ALLOWED_STAFF_IDS---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/fetch_allowed_staff_ids 2>/dev/null || echo "FAIL"
echo ""
echo "---FETCH_BASE_SALARIES---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/fetch_base_salaries 2>/dev/null || echo "FAIL"
echo ""
echo "---API_ENDPOINTS_LISTING---"
curl -s http://localhost:8000/openapi.json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); [print(p, list(v.keys())) for p,v in d.get('paths',{}).items()]" 2>/dev/null || echo "NO_OPENAPI"
  `, 120000);
  fs.writeFileSync('/home/node/.openclaw/workspace/audit/api_tests.txt', apiTests);
  console.log(apiTests);

  // Step 5: Check if API server is running
  console.log('=== CHECKING API SERVER ===');
  let serverStatus = await sshExec('systemctl is-active psvibe-api 2>/dev/null || echo "NO_SERVICE"; ps aux | grep uvicorn 2>/dev/null | grep -v grep || echo "NO_UVICORN"; ls /root/psvibe-sale-bot/api/ 2>/dev/null | head -30 || echo "NO_API_DIR"');
  fs.writeFileSync('/home/node/.openclaw/workspace/audit/server_status.txt', serverStatus);
  console.log(serverStatus);

  // Step 6: List all Python files and API routes
  console.log('=== LISTING API ROUTES ===');
  let apiRoutes = await sshExec(`
find /root/psvibe-sale-bot -name "*.py" -path "*/api*" -exec echo "FILE: {}" \\; -exec grep -n "app\\.\\(get\\|post\\|put\\|delete\\|patch\\)" {} \\; 2>/dev/null | head -200
echo "---ALSO---"
grep -rn "@router\\.\\(get\\|post\\|put\\|delete\\|patch\\)" /root/psvibe-sale-bot/api/ 2>/dev/null | head -200
  `);
  fs.writeFileSync('/home/node/.openclaw/workspace/audit/api_routes.txt', apiRoutes);
  console.log(apiRoutes);

  // Step 7: Get Google Sheet info via gspread
  console.log('=== GOOGLE SHEET INFO ===');
  let sheetInfo = await sshExec(`
cd /root/psvibe-sale-bot && python3 << 'PYEOF'
import os, json
from dotenv import load_dotenv
load_dotenv()
sheet_id = os.getenv('SHEET_ID') or os.getenv('GOOGLE_SHEET_ID') or os.getenv('SPREADSHEET_ID')
print(f"Sheet ID from env: {sheet_id}")

try:
    import gspread
    from google.oauth2.service_account import Credentials
    creds_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or '/root/psvibe-sale-bot/credentials.json'
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    client = gspread.authorize(creds)
    sh = client.open_by_key(sheet_id)
    worksheets = sh.worksheets()
    print(f"\\n=== SHEET TABS ({len(worksheets)}) ===")
    for ws in worksheets:
        print(f"  - {ws.title} (rows={ws.row_count}, cols={ws.col_count})")
    # Get first 2 rows of each sheet for column headers
    for ws in worksheets[:15]:
        try:
            rows = ws.get_all_values()
            if rows:
                print(f"\\n--- {ws.title} headers (row 1-2) ---")
                print(f"  Row1: {rows[0][:15]}")
                if len(rows) > 1:
                    print(f"  Row2: {rows[1][:15]}")
        except Exception as e:
            print(f"  {ws.title}: ERROR - {e}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
PYEOF
`, 30000);
  fs.writeFileSync('/home/node/.openclaw/workspace/audit/sheet_info.txt', sheetInfo);
  console.log(sheetInfo);

  console.log('=== DONE ===');
}

main().catch(err => { console.error(err); process.exit(1); });
