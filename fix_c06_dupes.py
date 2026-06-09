#!/usr/bin/env python3
"""Check and fix C-06 duplicates."""
import json, os
import urllib.request

api_key = os.environ.get("API_KEY", "")
url = f"http://localhost:8000/api/fetch_console_games?api_key={api_key}"
resp = urllib.request.urlopen(url, timeout=5)
data = json.loads(resp.read().decode())
games = data.get("data", {}).get("console_games", [])
c06 = [g for g in games if g["console_id"] == "C-06"]
print(f"C-06 has {len(c06)} records")

from collections import Counter
titles = [g["game_title"] for g in c06]
for t, c in Counter(titles).items():
    if c > 1:
        print(f'  DUPLICATE: "{t}" appears {c} times')
    print(f'  {t}: {c}x')

# Find fake entries (console names)
for g in c06:
    if g["game_title"] in ["C-06", "C06", "C 06"]:
        print(f'  FAKE ENTRY: "{g["game_title"]}" is a console ID!')

# Now fix: remove duplicates from DB
# Find the IDs of the duplicate entries
print("\n--- Finding duplicate record IDs ---")
for i, g in enumerate(c06):
    print(f"  [{i}] title={g['game_title']!r}, created_at={g['created_at'][:19]}")
