import paramiko, json, os, sys

key = paramiko.RSAKey.from_private_key_file('/home/node/.openclaw/workspace/.ssh/id_rsa')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('5.223.81.16', username='root', pkey=key, timeout=10)

# Check if Bot_Users sheet exists via gspread
stdin, stdout, stderr = client.exec_command('''
cd /root/psvibe_api_server
source /etc/psvibe/secrets.env
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/root/psvibe_api_server')
from sheets_client import _get_sh
try:
    sh = _get_sh()
    worksheets = sh.worksheets()
    names = [ws.title for ws in worksheets]
    print("All worksheets:", names)
    if "Bot_Users" in names:
        ws = sh.worksheet("Bot_Users")
        print(f"Bot_Users has {ws.row_count} rows, {ws.col_count} cols")
        print(f"Headers: {ws.row_values(1)}")
        if ws.row_count > 1:
            for r in range(max(1, ws.row_count-2), ws.row_count+1):
                print(f"  Row {r}: {ws.row_values(r)}")
    else:
        print("Bot_Users sheet NOT found in main spreadsheet")
        # Check if there's a separate sheet ID for it
        print("Looking for alternative sheet references...")
except Exception as e:
    print(f"Error: {e}")
PYEOF
''')
print(stdout.read().decode())
print(stderr.read().decode()[:500])
client.close()
