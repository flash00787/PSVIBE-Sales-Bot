import paramiko

key = paramiko.RSAKey.from_private_key_file('/home/node/.openclaw/workspace/.ssh/id_rsa')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('5.223.81.16', username='root', pkey=key, timeout=15)

# Upload and run a Python update script on VPS
update_script = r'''
import re, os

os.chdir("/root/psvibe_api_server")

with open("app.py", "r") as f:
    content = f.read()

old = '''@app.post("/api/bot-users/track", response_model=GenericResponse, tags=["Bot Users"], summary="Track bot user interaction")
async def api_bot_users_track(req: dict, auth=Depends(verify_api_key)):
    """Fire-and-forget: upsert bot user tracking row."""
    try:
        tg_id = req.get("tg_id", "")
        username = req.get("username", "")
        user_name = req.get("user_name", "")
        action = req.get("action", "")
        logger.info("BOT-USER: tg=%s user=%s action=%s", tg_id, user_name, action)
        return ok({"tracked": True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))'''

new = '''@app.post("/api/bot-users/track", response_model=GenericResponse, tags=["Bot Users"], summary="Track bot user interaction")
async def api_bot_users_track(req: dict, auth=Depends(verify_api_key)):
    """Fire-and-forget: upsert bot user tracking row to Bot_Users sheet."""
    try:
        tg_id = req.get("tg_id", "")
        username = req.get("username", "")
        user_name = req.get("user_name", "")
        action = req.get("action", "")
        member_id = req.get("member_id", "")
        phone = req.get("phone", "")
        logger.info("BOT-USER: tg=%s user=%s action=%s", tg_id, user_name, action)
        # Write to Bot_Users sheet (fire-and-forget)
        try:
            from sheets_client import get_worksheet
            ws = get_worksheet("Bot_Users")
            from datetime import datetime, timezone
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            ws.append_row([ts, str(tg_id), username or "", user_name or "", action or "", member_id or "", phone or ""])
        except Exception as se:
            logger.warning("Bot_Users sheet write failed: %s", se)
        return ok({"tracked": True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))'''

if old in content:
    content = content.replace(old, new, 1)
    with open("app.py", "w") as f:
        f.write(content)
    print("UPDATE SUCCESSFUL")
else:
    print("OLD TEXT NOT FOUND")
    # Debug: find the lines
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "bot-users/track" in line:
            print(f"  Found at line {i+1}: {line}")
            for j in range(i, min(i+15, len(lines))):
                print(f"    {j+1}: {lines[j]}")
'''

stdin, stdout, stderr = client.exec_command('cat > /tmp/update_track.py << \'SCRIPT\'\n' + update_script + '\nSCRIPT\npython3 /tmp/update_track.py')
print(stdout.read().decode()[:3000])
err = stderr.read().decode()
if err.strip():
    print("ERR:", err[:500])
client.close()
