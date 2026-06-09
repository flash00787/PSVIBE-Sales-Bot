const { Client } = require('ssh2');
const fs = require('fs');

const script = `import os, json, re

try:
    import gspread
    from google.oauth2.service_account import Credentials
    
    cred_paths = []
    for root, dirs, files in os.walk('/root/psvibe-sale-bot'):
        for f in files:
            if f.endswith('.json') and 'cred' in f.lower():
                cred_paths.append(os.path.join(root, f))
    
    print("Cred paths found:", cred_paths)
    
    with open('/root/psvibe-sale-bot/bot/__init__.py') as fh:
        content = fh.read()
    
    match = re.search(r'open_by_key\\(.*?\\)', content)
    sheet_id = None
    if match:
        sid = match.group(1).strip("'\\"")
        print("Sheet ID pattern found:", sid)
        sheet_id = sid
    
    # Also check env
    for line in content.split('\\n'):
        if 'SHEET_ID' in line:
            print("SHEET_ID line:", line.strip()[:200])
    
    if sheet_id and cred_paths:
        for cp in cred_paths[:1]:
            try:
                creds = Credentials.from_service_account_file(cp, scopes=['https://www.googleapis.com/auth/spreadsheets'])
                client = gspread.authorize(creds)
                sh = client.open_by_key(sheet_id)
                worksheets = sh.worksheets()
                print()
                print("=== ALL TABS (%d worksheets) ===" % len(worksheets))
                for ws in worksheets:
                    print("  '%s' (rows=%d, cols=%d)" % (ws.title, ws.row_count, ws.col_count))
                
                key_sheets = ['Sales_Daily', 'Setting', 'Card_Wallet', 'Stock_Out', 'Stock_In', 
                             'TopUp_Log', 'Inventory', 'Attendance_Log', 'Console_Booking',
                             'Salary_Advance', 'Game_Library', 'Console_Games']
                for ks in key_sheets:
                    try:
                        ws = sh.worksheet(ks)
                        rows = ws.get_all_values()
                        if rows:
                            print()
                            print("--- '%s' headers (%d data rows) ---" % (ks, len(rows)-1))
                            print("  Row1 (len=%d): %s" % (len(rows[0]), rows[0][:20]))
                            if len(rows) > 1:
                                print("  Row2: %s" % rows[1][:20])
                    except Exception as e:
                        print("  '%s': NOT FOUND - %s" % (ks, e))
                break
            except Exception as e:
                print("Cred %s: %s" % (cp, e))
    else:
        print("No sheet_id or cred_paths")
except Exception as e:
    print("ERROR:", e)
    import traceback
    traceback.print_exc()
`;

const conn = new Client();
let result = '';
conn.on('ready', () => {
  // Write script to VPS
  conn.exec(`cat > /tmp/gspread_check.py << 'SCRIPTEOF'
${script}
SCRIPTEOF
python3 /tmp/gspread_check.py`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    stream.on('data', (d) => { result += d.toString(); });
    stream.stderr.on('data', (d) => { result += d.toString(); });
    stream.on('close', () => { 
      fs.writeFileSync('/home/node/.openclaw/workspace/audit/sheet_gspread.txt', result);
      console.log(result);
      conn.end(); 
    });
  });
});
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
