#!/usr/bin/env python3
"""Fix sheets/log to write to dedicated AI_Chat_Log sheet."""
import os

os.chdir("/root/psvibe_api_server")

# Backup
os.system("cp app.py app.py.bak.4")

with open("app.py", "r") as f:
    content = f.read()

# Replace the sheets/log endpoint body
old_log_body = """    """Fire-and-forget: log an AI interaction row to Bot_Users sheet."""
    try:
        tg_id = req.get("tg_id", "")
        username = req.get("username", "")
        user_name = req.get("user_name", "")
        query = req.get("query", "")[:300]
        response = req.get("response", "")[:500]
        sentiment = req.get("sentiment", "neutral")
        logger.info("AI-LOG: user=%s query=%s sentiment=%s", user_name, query[:60], sentiment)
        try:
            from sheets_client import get_worksheet
            ws = get_worksheet("Input_Log")
            from datetime import datetime, timezone
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            ws.append_row([ts, str(tg_id), username or '', user_name or '', 'ai_chat', '', '', query, response, sentiment])
        except Exception as se:
            logger.warning("Input_Log sheet write failed: %s", se)
        return ok({"logged": True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))"""

new_log_body = '''    """Fire-and-forget: log an AI interaction row to AI_Chat_Log sheet."""
    try:
        tg_id = req.get("tg_id", "")
        username = req.get("username", "")
        user_name = req.get("user_name", "")
        query = req.get("query", "")[:300]
        response = req.get("response", "")[:500]
        sentiment = req.get("sentiment", "neutral")
        logger.info("AI-LOG: user=%s query=%s sentiment=%s", user_name, query[:60], sentiment)
        try:
            from sheets_client import get_worksheet
            ws = get_worksheet("AI_Chat_Log")
            # Auto-add headers if empty
            if ws.row_count == 0:
                ws.append_row(["Timestamp", "TG ID", "Username", "Full Name", "Query", "Response", "Sentiment"])
            from datetime import datetime, timezone
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            ws.append_row([ts, str(tg_id), username or "", user_name or "", query, response, sentiment])
        except Exception as se:
            logger.warning("AI_Chat_Log sheet write failed: %s", se)
        return ok({"logged": True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))'''

if old_log_body in content:
    content = content.replace(old_log_body, new_log_body, 1)
    with open("app.py", "w") as f:
        f.write(content)
    print("UPDATE OK")
else:
    print("OLD TEXT NOT FOUND - checking actual content...")
    with open("app.py", "r") as f:
        for i, line in enumerate(f):
            if "sheets/log" in line:
                print(f"  Line {i+1}: {line.rstrip()[:100]}")
