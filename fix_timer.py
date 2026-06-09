#!/usr/bin/env python3
"""Fix _is_session_active to handle list response from _replit_get_async."""
FILE = "/root/psvibe-sales-bot/bot/handlers/booking_flow.py"
with open(FILE) as f:
    code = f.read()

old = """async def _is_session_active(cid: str) -> bool:
    \"\"\"Quick sync check: is this console Active today? (via MySQL API).\"\"\"
    try:
        # Use fetch_console_status endpoint (console_booking endpoint doesn't exist)
        bk_data = await _replit_get_async("fetch_console_status")
        if bk_data and isinstance(bk_data, dict):
            consoles = bk_data.get("consoles", bk_data.get("data", []))
            if isinstance(consoles, list):
                for row in consoles:
                    if isinstance(row, dict) and row.get("console_id", "").strip() == cid and row.get("status", "").strip() == "Active":
                        return True
            elif isinstance(consoles, dict):
                for row in consoles.get("consoles", []):
                    if isinstance(row, dict) and row.get("console_id", "").strip() == cid and row.get("status", "").strip() == "Active":
                        return True
    except Exception as e:
        logger.error("_is_session_active: %s", e, exc_info=True)
        return True
    return False"""

new = """async def _is_session_active(cid: str) -> bool:
    \"\"\"Quick sync check: is this console Active today? (via MySQL API).\"\"\"
    try:
        # Use fetch_console_status endpoint - _replit_get_async returns list of dicts
        bk_data = await _replit_get_async("fetch_console_status")
        if isinstance(bk_data, list):
            for row in bk_data:
                if isinstance(row, dict) and row.get("console_id", "").strip() == cid and row.get("status", "").strip() == "Active":
                    return True
        elif isinstance(bk_data, dict):
            consoles = bk_data.get("consoles", bk_data.get("data", []))
            if isinstance(consoles, list):
                for row in consoles:
                    if isinstance(row, dict) and row.get("console_id", "").strip() == cid and row.get("status", "").strip() == "Active":
                        return True
            elif isinstance(consoles, dict):
                for row in consoles.get("consoles", []):
                    if isinstance(row, dict) and row.get("console_id", "").strip() == cid and row.get("status", "").strip() == "Active":
                        return True
    except Exception as e:
        logger.error("_is_session_active: %s", e, exc_info=True)
        return True
    return False"""

if old in code:
    code = code.replace(old, new, 1)
    with open(FILE, "w") as f:
        f.write(code)
    compile(code, FILE, "exec")
    print("✅ booking_flow.py: _is_session_active now handles list response")
else:
    print("❌ Pattern not found")
    # Find the function
    idx = code.find("def _is_session_active")
    if idx >= 0:
        end = code.find("\n    return False", idx) + len("\n    return False")
        print(f"Found at {idx}, length {end-idx}")
        print(code[idx:end])
