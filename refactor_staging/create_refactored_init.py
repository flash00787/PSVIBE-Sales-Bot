#!/usr/bin/env python3
"""Create the Phase 6 refactored __init__.py with IntEnum states and __all__."""
import re

with open("/home/node/.openclaw/workspace/refactor_staging/__init__.py", "r") as f:
    content = f.read()

# ── 1. Add IntEnum import ──────────────────────────────────────────────
if "from enum import IntEnum" not in content:
    content = content.replace(
        "from datetime import datetime, timezone, timedelta",
        "from datetime import datetime, timezone, timedelta\nfrom enum import IntEnum"
    )

# ── 2. Extract state names ─────────────────────────────────────────────
lines = content.split("\n")
in_states = False
state_names = []
for i, line in enumerate(lines):
    if "STATES" in line:
        in_states = True
        continue
    if in_states:
        if "= range(177)" in line:
            break
        comment_pos = line.find("#")
        clean = line[:comment_pos] if comment_pos >= 0 else line
        matches = re.findall(r"\b([A-Z][A-Z0-9_]+)\b", clean)
        for m in matches:
            if m not in state_names:
                state_names.append(m)

print(f"Found {len(state_names)} state constants")

# ── 3. Build IntEnum class ────────────────────────────────────────────
enum_lines = [
    "",
    "class BotState(IntEnum):",
    '    """Bot conversation states with integer values for ConversationHandler."""',
]
for i, name in enumerate(state_names):
    enum_lines.append(f"    {name} = {i}")
enum_lines.append("")

# ── 4. Build module-level aliases for backward compatibility ──────────
alias_lines = ["# ── Module-level aliases for backward compatibility ──"]
for name in state_names:
    alias_lines.append(f"{name} = BotState.{name}")
alias_lines.append("")

# ── 5. Find and replace the old state declaration ──────────────────────
old_start = None
old_end = None
for i, line in enumerate(lines):
    if "STATES" in line:
        old_start = i
    if old_start is not None and "= range(177)" in line:
        old_end = i + 1
        break

if old_start is not None and old_end is not None:
    # Delete lines from old_start to old_end-1
    new_lines = lines[:old_start]
    new_lines.extend(enum_lines)
    new_lines.extend(alias_lines)
    new_lines.extend(lines[old_end:])
    content = "\n".join(new_lines)
    print(f"Replaced state declaration (lines {old_start+1}-{old_end})")
else:
    print("WARNING: Could not find state declaration!")

# ── 6. Add __all__ for explicit star-import control ────────────────────
# Collect all public names (don't start with _) and select _prefixed names needed
all_names = []
public_prefixes = [
    "BTN_", "N8N_", "MMT", "BOT_VERSION", "VALID_CONSOLES", "NAV_ROW",
    "RANK_EMOJI", "RECEIPTS_DIR", "SSD_NAMES", "SSD_BTN_TO_ID",
    "STOCK_ACCESS_PIN", "CUSTOMER_BOT_TOKEN", "STAFF_NOTIFY_CHAT",
]

# Scan for all public names defined after the imports
for line in content.split("\n"):
    # Match module-level assignments
    m = re.match(r'^([A-Z][A-Z0-9_]+)\s*=', line)
    if m:
        all_names.append(m.group(1))
    # Match def statements
    m = re.match(r'^(?:async\s+)?def\s+([a-z_][a-z0-9_]*)\s*\(', line)
    if m:
        fn_name = m.group(1)
        if not fn_name.startswith("_"):
            all_names.append(fn_name)

# Add BotState and its members
all_names.append("BotState")
for name in state_names:
    if name not in all_names:
        all_names.append(name)

# Deduplicate while preserving order
seen = set()
unique_names = []
for name in all_names:
    if name not in seen:
        seen.add(name)
        unique_names.append(name)

# Write __all__ before the first import
all_declaration = f"\n__all__ = {repr(unique_names)}\n"
# Insert after the docstring block but before imports
# Find the position after 'BOT_VERSION = ' line
insert_pos = content.find("BOT_VERSION")
if insert_pos > 0:
    # Find end of that line
    end_of_line = content.find("\n", insert_pos)
    content = content[:end_of_line+1] + all_declaration + content[end_of_line+1:]
    print(f"Added __all__ with {len(unique_names)} names")
else:
    print("WARNING: Could not find BOT_VERSION line for __all__ insertion")

# ── 7. Fix the handlers import to use explicit path ─────────────────────
# Replace "from bot.handlers import *" with "from bot.handlers import *" (keep as-is for now)
# The star import is controlled by __all__ now

# ── 8. Write output ────────────────────────────────────────────────────
outpath = "/home/node/.openclaw/workspace/refactor_staging/__init___refactored.py"
with open(outpath, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n✅ Written refactored __init__.py → {outpath}")
print(f"   - BotState IntEnum with {len(state_names)} states")
print(f"   - __all__ with {len(unique_names)} exported names")
print(f"   - Module-level aliases for backward compatibility")
