#!/usr/bin/env python3
"""Fix fetch_games_async to return list[dict] instead of raw API dict."""

PFILE = "/root/psvibe-sales-bot/bot/__init__.py"

with open(PFILE) as f:
    code = f.read()

old = "    fetch_games_async = api_fetch_games_async"
new = """async def fetch_games_async() -> list[dict]:
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

if old in code:
    code = code.replace(old, new, 1)
    with open(PFILE, "w") as f:
        f.write(code)
    
    import py_compile
    py_compile.compile(PFILE, doraise=True)
    print("OK - fetch_games_async now returns list[dict] with mapped fields")
else:
    print("ERROR: Pattern not found in file")
