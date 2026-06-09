#!/usr/bin/env python3
"""Update sheets/log endpoint to write to Bot_Users sheet."""
import os

os.chdir("/root/psvibe_api_server")

with open("app.py", "r") as f:
    content = f.read()

lines = content.split("\n")
start = None
for i, line in enumerate(lines):
    if 'sheets/log' in line and '@app.post' in line:
        start = i
        break

if start is None:
    print("ERROR: sheets/log endpoint not found")
    exit(1)

end = start + 1
while end < len(lines):
    if lines[end].strip().startswith("@app."):
        break
    end += 1

print(f"Found endpoint at lines {start+1} to {end}")

new_func = [
    '@app.post("/api/sheets/log", response_model=GenericResponse, tags=["Logging"], summary="Log AI interaction")',
    'async def api_sheets_log(req: dict, auth=Depends(verify_api_key)):',
    '    """Fire-and-forget: log an AI interaction row to Bot_Users sheet."""',
    "    try:",
    '        tg_id = req.get("tg_id", "")',
    '        username = req.get("username", "")',
    '        user_name = req.get("user_name", "")',
    '        query = req.get("query", "")[:300]',
    '        response = req.get("response", "")[:500]',
    '        sentiment = req.get("sentiment", "neutral")',
    '        logger.info("AI-LOG: user=%s query=%s sentiment=%s", user_name, query[:60], sentiment)',
    "        try:",
    "            from sheets_client import get_worksheet",
    '            ws = get_worksheet("Input_Log")',
    "            from datetime import datetime, timezone",
    '            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")',
    "            ws.append_row([ts, str(tg_id), username or '', user_name or '', 'ai_chat', '', '', query, response, sentiment])",
    "        except Exception as se:",
    '            logger.warning("Input_Log sheet write failed: %s", se)',
    '        return ok({"logged": True})',
    "    except Exception as e:",
    "        raise HTTPException(status_code=500, detail=str(e))",
]

new_content = "\n".join(lines[:start]) + "\n" + "\n".join(new_func) + "\n\n" + "\n".join(lines[end:])

with open("app.py", "w") as f:
    f.write(new_content)

print("UPDATE OK - sheets/log updated")
