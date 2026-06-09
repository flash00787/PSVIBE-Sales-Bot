const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
let result = '';
conn.on('ready', () => {
  conn.exec(`grep SHEET_ID /root/psvibe-sale-bot/.env && python3 << 'SCRIPTEOF'
import os, json, gspread
from google.oauth2.service_account import Credentials

# Read .env directly
with open('/root/psvibe-sale-bot/.env') as f:
    for line in f:
        line = line.strip()
        if line.startswith('SHEET_ID='):
            sheet_id = line.split('=', 1)[1].strip().strip('"').strip("'")
            print("SHEET_ID:", sheet_id)
            break

creds = Credentials.from_service_account_file(
    '/root/psvibe-sale-bot/service_account.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
client = gspread.authorize(creds)
sh = client.open_by_key(sheet_id)
worksheets = sh.worksheets()
print()
print("=== ALL TABS (%d) ===" % len(worksheets))
for ws in worksheets:
    print("  '%s' (rows=%d, cols=%d)" % (ws.title, ws.row_count, ws.col_count))

key_sheets = ['Sales_Daily', 'Setting', 'Card_Wallet', 'Stock_Out', 'Stock_In', 
             'TopUp_Log', 'Inventory', 'Attendance_Log', 'Console_Booking',
             'Salary_Advance', 'Game_Library', 'Console_Games']
print()
print("=== HEADER VERIFICATION ===")
for ks in key_sheets:
    try:
        ws = sh.worksheet(ks)
        rows = ws.get_all_values()
        if rows:
            r1 = rows[0]
            print()
            print("--- '%s' (%d data rows, %d cols) ---" % (ks, len(rows)-1, len(r1)))
            print("  Headers: %s" % r1)
            if len(rows) > 1:
                print("  Row2:    %s" % rows[1])
    except Exception as e:
        print("  '%s': NOT FOUND - %s" % (ks, e))

# Check specific cells referenced in code
print()
print("=== SPECIFIC CELL CHECKS ===")
try:
    ws = sh.worksheet('Setting')
    # setting_sh.cell(1, 19) - col S header
    print("Setting S1 (col 19):", ws.cell(1, 19).value)
    print("Setting T1 (col 20):", ws.cell(1, 20).value)
    print("Setting S2:", ws.cell(2, 19).value)
    print("Setting T2:", ws.cell(2, 20).value)
    # setting_sh.cell(30, 2) - B30 allowed staff
    print("Setting B30 (allowed staff):", ws.cell(30, 2).value)
    # setting_sh.cell(2, 2) - B2 base rate?
    print("Setting B2 (base rate?):", ws.cell(2, 2).value)
    # setting_sh.cell(20, 2) - B20 food price
    print("Setting B20 (food price?):", ws.cell(20, 2).value)
    print("Setting B21 (food mins?):", ws.cell(21, 2).value)
    # setting_sh.col_values(8) - H = console names
    h_vals = ws.col_values(8)[:5]
    print("Setting H (console names, first 5):", h_vals)
    # setting_sh.col_values(10) - J = multipliers
    j_vals = ws.col_values(10)[:5]
    print("Setting J (multipliers, first 5):", j_vals)
    # setting_sh.col_values(4) - D = food names
    d_vals = ws.col_values(4)[:5]
    print("Setting D (food names, first 5):", d_vals)
    # setting_sh.col_values(5) - E = food prices
    e_vals = ws.col_values(5)[:5]
    print("Setting E (food prices, first 5):", e_vals)
    # setting_sh.col_values(6) - F = food costs
    f_vals = ws.col_values(6)[:5]
    print("Setting F (food costs, first 5):", f_vals)
    # O2:R5 - rank thresholds
    o_r = ws.get("O2:R5")
    print("Setting O2:R5 (rank thresholds):", o_r)
    # O1:R1 headers
    o_h = ws.get("O1:R1")
    print("Setting O1:R1 (rank headers):", o_h)
    # M3 (master) and M4 (immortal)
    print("Setting M3 (master threshold?):", ws.cell(3, 13).value)
    print("Setting M4 (immortal threshold?):", ws.cell(4, 13).value)
except Exception as e:
    print("Setting cell check error:", e)

try:
    ws = sh.worksheet('Card_Wallet')
    print()
    print("--- Card_Wallet ---")
    # Col A = row_no, Col B = member_id, Col K (11) = effective_rate?
    # Col Q (17) = referral_code
    print("Card_Wallet headers:", ws.row_values(1))
    print("A1:", ws.cell(1,1).value)
    print("K1 (col 11):", ws.cell(1,11).value)
    print("L1 (col 12):", ws.cell(1,12).value)
    print("Q1 (col 17):", ws.cell(1,17).value)
    # Col H (8) = wallet_mins
    print("H1 (col 8):", ws.cell(1,8).value)
    if ws.row_count > 1:
        print("Row 2 data:", ws.row_values(2)[:17])
except Exception as e:
    print("Card_Wallet error:", e)
SCRIPTEOF`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    stream.on('data', (d) => { result += d.toString(); });
    stream.stderr.on('data', (d) => { result += d.toString(); });
    stream.on('close', () => { 
      fs.writeFileSync('/home/node/.openclaw/workspace/audit/sheet_verify.txt', result);
      console.log(result);
      conn.end(); 
    });
  });
});
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
