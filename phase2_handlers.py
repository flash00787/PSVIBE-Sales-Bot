#!/usr/bin/env python3
"""Apply Task 5 bare-except logging to bot/handlers.py - critical business ops only."""
filepath = "/root/Sales-Tele-Bot_staging/bot/handlers.py"
with open(filepath, "r") as f:
    content = f.read()

print(f"Original length: {len(content)}, lines: {content.count(chr(10))}")

edits = 0

# 1. Console status fetch in booking flow (select console step, line ~1322)
old = "    try:\n        _cons = [c[\"id\"] for c in fetch_console_status()]\n    except Exception:\n        _cons = sorted(VALID_CONSOLES)"
new = "    try:\n        _cons = [c[\"id\"] for c in fetch_console_status()]\n    except Exception as e:\n        logging.warning(\"Failed to fetch console status for booking keyboard: %s\", e)\n        _cons = sorted(VALID_CONSOLES)"
if old in content:
    content = content.replace(old, new, 1)
    edits += 1
    print("OK console_fetch_1")

# 2. Console status fetch in _check_member_in_session (line ~1669)
old = "    try:\n        consoles = fetch_console_status()\n    except Exception:\n        return await prompt_console(update, context)\n\n    actives = [\n        c for c in consoles\n        if c.get(\"member\") == member_id and c.get(\"status\") in (\"Active\", \"Scheduled\")"
new = "    try:\n        consoles = fetch_console_status()\n    except Exception as e:\n        logging.warning(\"Failed to fetch console status for member session check: %s\", e)\n        return await prompt_console(update, context)\n\n    actives = [\n        c for c in consoles\n        if c.get(\"member\") == member_id and c.get(\"status\") in (\"Active\", \"Scheduled\")"
if old in content:
    content = content.replace(old, new, 1)
    edits += 1
    print("OK console_fetch_2")

# 3. Console status fetch in _check_console_in_session (line ~1824)
old = "    try:\n        consoles = fetch_console_status()\n    except Exception:\n        return await prompt_mins(update, context)\n\n    active = next("
new = "    try:\n        consoles = fetch_console_status()\n    except Exception as e:\n        logging.warning(\"Failed to fetch console status for console session check: %s\", e)\n        return await prompt_mins(update, context)\n\n    active = next("
if old in content:
    content = content.replace(old, new, 1)
    edits += 1
    print("OK console_fetch_3")

# 4. _sbk_console_kb API fetch failure (line ~6575)
old = "    try:\n        data = _replit_get(\"sheets/consoles\")\n        consoles = data.get(\"consoles\", []) if isinstance(data, dict) else []\n    except Exception:\n        consoles = []"
new = "    try:\n        data = _replit_get(\"sheets/consoles\")\n        consoles = data.get(\"consoles\", []) if isinstance(data, dict) else []\n    except Exception as e:\n        logging.warning(\"Failed to fetch consoles via API for staff booking keyboard: %s\", e)\n        consoles = []"
if old in content:
    content = content.replace(old, new, 1)
    edits += 1
    print("OK sbk_console_kb")

# 5. _sbk_console_kb fallback fetch_console_status (line ~6582)
old = "        try:\n            consoles = [{\"id\": c[\"id\"], \"type\": c.get(\"type\",\"\"), \"liveStatus\": c.get(\"status\",\"Free\")}\n                        for c in fetch_console_status()]\n        except Exception:\n            return [[c] for c in sorted(VALID_CONSOLES)] + [[BTN_BACK, BTN_CANCEL]]"
new = "        try:\n            consoles = [{\"id\": c[\"id\"], \"type\": c.get(\"type\",\"\"), \"liveStatus\": c.get(\"status\",\"Free\")}\n                        for c in fetch_console_status()]\n        except Exception as e:\n            logging.warning(\"Failed to fetch console status (staff booking fallback): %s\", e)\n            return [[c] for c in sorted(VALID_CONSOLES)] + [[BTN_BACK, BTN_CANCEL]]"
if old in content:
    content = content.replace(old, new, 1)
    edits += 1
    print("OK sbk_console_kb_fallback")

# 6. Validate console IDs in staff booking flow (line ~6748)
old = "    try:\n        all_c = fetch_console_status()\n        valid = {c[\"id\"] for c in all_c}\n    except Exception:\n        valid = VALID_CONSOLES"
new = "    try:\n        all_c = fetch_console_status()\n        valid = {c[\"id\"] for c in all_c}\n    except Exception as e:\n        logging.warning(\"Failed to validate console IDs (staff booking): %s\", e)\n        valid = VALID_CONSOLES"
if old in content:
    content = content.replace(old, new, 1)
    edits += 1
    print("OK validate_console")

# 7. fetch_members in staff booking flow (line ~6760)
old = "    try:\n        members = fetch_members()\n    except Exception:\n        members = []\n    kb = [[\"\U0001f464 Guest (Walk-in)\"]]"
new = "    try:\n        members = fetch_members()\n    except Exception as e:\n        logging.warning(\"Failed to fetch members for staff booking: %s\", e)\n        members = []\n    kb = [[\"\U0001f464 Guest (Walk-in)\"]]"
if old in content:
    content = content.replace(old, new, 1)
    edits += 1
    print("OK fetch_members")

# 8. fetch_games in staff booking (line ~6954)
old = "    try:\n        games = fetch_games()\n        game_names = [g[\"title\"] for g in games if g.get(\"title\")][:30]\n    except Exception:\n        game_names = []"
new = "    try:\n        games = fetch_games()\n        game_names = [g[\"title\"] for g in games if g.get(\"title\")][:30]\n    except Exception as e:\n        logging.warning(\"Failed to fetch games for staff booking: %s\", e)\n        game_names = []"
if old in content:
    content = content.replace(old, new, 1)
    edits += 1
    print("OK fetch_games")

# Write
with open(filepath, "w") as f:
    f.write(content)

print(f"Total edits: {edits}")
print(f"Final length: {len(content)}, lines: {content.count(chr(10))}")
print("DONE: bot/handlers.py Phase 2 modifications complete")
