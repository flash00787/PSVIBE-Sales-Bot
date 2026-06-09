#!/usr/bin/env python3
"""Fix ALL async functions - console_games and console_status."""
PFILE = "/root/psvibe-sales-bot/bot/__init__.py"
with open(PFILE) as f:
    code = f.read()

# Remove alias line for console_games_async
old1 = "    fetch_console_games_async = api_fetch_console_games_async\n"
if old1 in code:
    code = code.replace(old1, "", 1)
    print("1. Removed console_games_async alias")

# Add proper async wrappers after except block
new_fn = """

async def fetch_console_games_async() -> list[dict]:
    \"\"\"Async version of fetch_console_games().\"\"\"
    result = await api_fetch_console_games_async()
    if result is None:
        return []
    mapped = []
    for g in result.get("console_games", []):
        mapped.append({
            "console_id":    g.get("console_id", ""),
            "console_name":   str(g.get("console_name", "")),
            "game_id":        g.get("game_id", ""),
            "game_title":     g.get("game_title", ""),
            "genre":          g.get("genre", ""),
            "status":         g.get("status", ""),
            "install_type":   g.get("install_type", ""),
            "slot_position":  str(g.get("slot_position", "")),
            "notes":          g.get("notes", ""),
        })
    return mapped


async def fetch_console_status_async() -> list[dict]:
    \"\"\"Async version of fetch_console_status().\"\"\"
    result = await api_fetch_console_status_async()
    if result is None:
        return []
    mapped = []
    for c in result.get("consoles", []):
        mapped.append({
            "id":        c.get("console_id", ""),
            "type":      c.get("console_type", ""),
            "mult":      1.0,
            "status":    c.get("status", "Free"),
            "member":    c.get("current_member"),
            "start":     c.get("start_time"),
            "staff":     c.get("staff_name"),
            "booking_id": c.get("booking_id"),
        })
    return mapped

"""

marker = "except ImportError:\n    _HAS_API = False\n\n"
if marker in code:
    code = code.replace(marker, marker + new_fn, 1)
    print("2. Added async wrappers after except block")

with open(PFILE, "w") as f:
    f.write(code)

import py_compile
py_compile.compile(PFILE, doraise=True)
print("3. SYNTAX OK")
