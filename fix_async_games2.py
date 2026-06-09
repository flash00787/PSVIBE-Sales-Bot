#!/usr/bin/env python3
"""Fix: place fetch_games_async AFTER the try/except block."""

PFILE = "/root/psvibe-sales-bot/bot/__init__.py"

with open(PFILE) as f:
    code = f.read()

# Step 1: Remove the broken async def that replaced the alias
# It might be at indent 0 or be the old alias line
old1 = """async def fetch_games_async() -> list[dict]:
    \"\"\"Async version of fetch_games().\"\"\"
    result = await api_fetch_games_async()
    if result is None:
        return []
    mapped = []
    for i, g in enumerate(result.get("games", [])):
        mapped.append({
            "row":        i + 2,
            "title":      g.get("game_title", ""),
            "status":     g.get("final_status", ""),
            "discs":      str(g.get("disc_count", "")),
            "solo_multi": g.get("solo_multi", ""),
            "genre":      g.get("genre", ""),
        })
    return mapped
"""

if old1 in code:
    code = code.replace(old1, "    fetch_games_async = api_fetch_games_async\n", 1)
    print("Step 1: Removed broken async def, restored alias")
elif "    fetch_games_async = api_fetch_games_async" in code:
    print("Step 1: Alias already exists, checking...")
else:
    print("Step 1: Neither found - manual check needed")
    # Show what's around line 63
    lines = code.split("\n")
    for i in range(55, 75):
        if i < len(lines):
            print(f"L{i+1}: {lines[i]}")

# Step 2: Add proper async wrapper AFTER the except ImportError block
marker = "except ImportError:\n    _HAS_API = False\n\n"
new_fn = """

async def fetch_games_async() -> list[dict]:
    \"\"\"Async version of fetch_games() - maps API data to GSheet-era format.\"\"\"
    result = await api_fetch_games_async()
    if result is None:
        return []
    mapped = []
    for i, g in enumerate(result.get("games", [])):
        mapped.append({
            "row":        i + 2,
            "title":      g.get("game_title", ""),
            "status":     g.get("final_status", ""),
            "discs":      str(g.get("disc_count", "")),
            "solo_multi": g.get("solo_multi", ""),
            "genre":      g.get("genre", ""),
        })
    return mapped

"""

if marker in code:
    code = code.replace(marker, marker + new_fn, 1)
    print("Step 2: Added async def after except block")
else:
    print(f"Step 2: Marker not found. Checking for variations...")
    import re
    m = re.search(r"except ImportError:\n\s+_HAS_API = False\n", code)
    if m:
        print(f"Found at: {repr(m.group())}")
    else:
        print("Cannot find the except block!")

with open(PFILE, "w") as f:
    f.write(code)

import py_compile
try:
    py_compile.compile(PFILE, doraise=True)
    print("SYNTAX OK!")
except py_compile.PyCompileError as e:
    print(f"SYNTAX ERROR: {e}")
    print("Restoring from backup...")
    import shutil
    shutil.copy2("/root/psvibe-sales-bot/bot/__init__.py.bak.mysql-migration", PFILE)
    print("Restored original")
