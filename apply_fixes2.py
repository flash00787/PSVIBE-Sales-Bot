#!/usr/bin/env python3
"""Apply remaining fixes to remote server."""
import paramiko, sys, os

HOST = "5.223.81.16"
KEY_PATH = os.path.expanduser("/home/node/.openclaw/workspace/.ssh/id_rsa")
USER = "root"

def connect():
    key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, pkey=key, timeout=15)
    return client

def remote_edit(client, filepath, old_text, new_text):
    """Apply a single edit to a remote file."""
    sftp = client.open_sftp()
    with sftp.file(filepath, 'r') as f:
        content = f.read().decode('utf-8', errors='replace')
    
    count = content.count(old_text)
    if count == 0:
        sftp.close()
        return f"FAIL: oldText NOT FOUND in {filepath}"
    if count > 1:
        sftp.close()
        return f"FAIL: oldText found {count} times (not unique) in {filepath}"
    
    content = content.replace(old_text, new_text, 1)
    
    with sftp.file(filepath, 'w') as f:
        f.write(content)
    sftp.close()
    return f"OK: edit applied to {filepath}"

client = connect()

# ================================================================
# FIX 4: fetch_games_async() — extract games list and map game_title → title
# ================================================================
old4 = """async def fetch_games_async() -> list[dict]:
    return await _replit_get_async(\"fetch_games\")"""

new4 = """async def fetch_games_async() -> list[dict]:
    \"\"\"Async version — maps API game_title → title for handler compatibility.\"\"\"
    data = await _replit_get_async(\"fetch_games\")
    if isinstance(data, dict) and \"games\" in data:
        raw_games = data[\"games\"]
    elif isinstance(data, list):
        raw_games = data
    else:
        return []
    return [{
        \"row\":        i + 2,
        \"title\":      g.get(\"game_title\", \"\"),
        \"status\":     g.get(\"final_status\", \"\"),
        \"discs\":      str(g.get(\"disc_count\", \"\")),
        \"solo_multi\": g.get(\"solo_multi\", \"\"),
        \"genre\":      g.get(\"genre\", \"\"),
    } for i, g in enumerate(raw_games) if isinstance(g, dict)]"""

result4 = remote_edit(client,
    "/root/psvibe-sales-bot/bot/__init__.py",
    old4, new4)
print(f"FIX 4: {result4}")

# Now restart all services
stdin, stdout, stderr = client.exec_command(
    "systemctl restart psvibe-sale-bot psvibe_customer_bot psvibe-api 2>&1; sleep 3; systemctl is-active psvibe-sale-bot psvibe_customer_bot psvibe-api", timeout=15)
out = stdout.read().decode('utf-8', errors='replace')
print(f"Restart: {out.strip()}")

client.close()
print("=== Fixes complete ===")
