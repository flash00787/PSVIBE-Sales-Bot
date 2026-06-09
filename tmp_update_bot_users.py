#!/usr/bin/env python3
"""Update bot-users/track endpoint to write to Bot_Users sheet."""
import os

os.chdir("/root/psvibe_api_server")

with open("app.py", "r") as f:
    content = f.read()

lines = content.split("\n")
start = None
for i, line in enumerate(lines):
    if "bot-users/track" in line:
        start = i
        break

if start is None:
    print("ERROR: bot-users/track endpoint not found")
    exit(1)

# Find end: next @app. line
end = start + 1
while end < len(lines):
    if lines[end].strip().startswith("@app."):
        break
    end += 1

print(f"Found endpoint at lines {start+1} to {end}")

new_func = [
    '@app.post("/api/bot-users/track", response_model=GenericResponse, tags=["Bot Users"], summary="Track bot user interaction")',
    'async def api_bot_users_track(req: dict, auth=Depends(verify_api_key)):',
    '    """Fire-and-forget: upsert bot user tracking row to Bot_Users sheet."""',
    "    try:",
    '        tg_id = req.get("tg_id", "")',
    '        username = req.get("username", "")',
    '        user_name = req.get("user_name", "")',
    '        action = req.get("action", "")',
    '        member_id = req.get("member_id", "")',
    '        phone = req.get("phone", "")',
    '        logger.info("BOT-USER: tg=%s user=%s action=%s", tg_id, user_name, action)',
    "        try:",
    "            from sheets_client import get_worksheet",
    '            ws = get_worksheet("Bot_Users")',
    "            from datetime import datetime, timezone",
    '            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")',
    "            ws.append_row([ts, str(tg_id), username or '', user_name or '', action or '', member_id or '', phone or ''])",
    "        except Exception as se:",
    '            logger.warning("Bot_Users sheet write failed: %s", se)',
    '        return ok({"tracked": True})',
    "    except Exception as e:",
    "        raise HTTPException(status_code=500, detail=str(e))",
]

new_content = "\n".join(lines[:start]) + "\n" + "\n".join(new_func) + "\n\n" + "\n".join(lines[end:])

with open("app.py", "w") as f:
    f.write(new_content)

print("UPDATE OK")
