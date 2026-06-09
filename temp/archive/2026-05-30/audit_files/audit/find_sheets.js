const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
let result = '';
conn.on('ready', () => {
  conn.exec(`cat > /tmp/gspread_check2.py << 'SCRIPTEOF'
import os, json, re, subprocess

# Find cred files
print("=== Looking for credential JSON files ===")
r = subprocess.run(['find', '/root/psvibe-sale-bot', '-name', '*.json', '-type', 'f'], capture_output=True, text=True)
print(r.stdout)

# Find env files
print("=== Looking for .env files ===")
r = subprocess.run(['find', '/root/psvibe-sale-bot', '-name', '.env*', '-o', '-name', '*.env'], capture_output=True, text=True)
print(r.stdout)

# Find sheet references in config
print("=== Grep for open_by_key ===")
r = subprocess.run(['grep', '-rn', 'open_by_key', '/root/psvibe-sale-bot/bot/__init__.py'], capture_output=True, text=True)
print(r.stdout)

print("=== Grep for wb ==")
r = subprocess.run(['grep', '-n', 'wb =|= gspread', '/root/psvibe-sale-bot/bot/__init__.py'], capture_output=True, text=True)
print(r.stdout)

print("=== Grep for SHEET_ID or spreadsheet ===")
r = subprocess.run(['grep', '-rni', 'sheet_id\\|spreadsheet', '/root/psvibe-sale-bot/bot/'], capture_output=True, text=True)
print(r.stdout)

# Try gspread
try:
    import gspread
    print("=== gspread available ===")
    # Try to find any active spreadsheet
    # Check if service account is configured
    r = subprocess.run(['find', '/root', '-name', '*.json', '-path', '*cred*', '-o', '-name', 'service*.json'], capture_output=True, text=True)
    print("More cred files:", r.stdout)
except Exception as e:
    print("gspread import error:", e)
SCRIPTEOF
python3 /tmp/gspread_check2.py`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    stream.on('data', (d) => { result += d.toString(); });
    stream.stderr.on('data', (d) => { result += d.toString(); });
    stream.on('close', () => { 
      fs.writeFileSync('/home/node/.openclaw/workspace/audit/sheet_find.txt', result);
      console.log(result);
      conn.end(); 
    });
  });
});
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
