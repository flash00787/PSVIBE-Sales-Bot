#!/usr/bin/env python3
"""Verify Bot_Users tracking setup."""
import paramiko, json, sys

key = paramiko.RSAKey.from_private_key_file('/home/node/.openclaw/workspace/.ssh/id_rsa')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('5.223.81.16', username='root', pkey=key, timeout=15)

# Check sheets
stdin, stdout, stderr = client.exec_command("""
cd /root/psvibe_api_server
source /etc/psvibe/secrets.env
export SHEET_ID=1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA
python3 << 'CHECKSHEET'
import gspread, os
from google.oauth2.service_account import Credentials
creds = Credentials.from_service_account_file('/root/psvibe_api_server/service_account.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
gc = gspread.authorize(creds)
sh = gc.open_by_key(os.environ['SHEET_ID'])
ws = sh.worksheet('Input_Log')
print('Input_Log headers:', ws.row_values(1))
print('Input_Log total rows:', ws.row_count)
ws2 = sh.worksheet('Bot_Users')
print('Bot_Users headers:', ws2.row_values(1))
print('Bot_Users total rows:', ws2.row_count)
CHECKSHEET
""")
print("SHEET CHECK:", stdout.read().decode()[:2000])
if stderr.channel.recv_stderr_ready():
    print("ERR:", stderr.read().decode()[:500])

# Test the API endpoint
stdin, stdout, stderr = client.exec_command("""
source /etc/psvibe/secrets.env
API_KEY=$(grep ^API_KEY /etc/psvibe/secrets.env | cut -d= -f2)
curl -s -X POST http://localhost:8000/api/bot-users/track \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"tg_id":"12345","username":"testuser","user_name":"Test User","action":"test","member_id":"","phone":""}'
""")
print("API TEST:", stdout.read().decode()[:500])
if stderr.channel.recv_stderr_ready():
    print("ERR:", stderr.read().decode()[:500])

client.close()
print("DONE")
