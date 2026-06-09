#!/usr/bin/env python3
"""Restore sales.py from backup and re-apply fixes."""
import re, sys

backup = sys.argv[1]
target = sys.argv[2]

with open(backup, 'r') as f:
    content = f.read()

# ── Fix 1: Remove game-select prompt_mins (lines 697-732) ──
# The game-select prompt_mins starts with:
pattern1 = r'\n\nasync def prompt_mins\(update: Update, context: ContextTypes\.DEFAULT_TYPE\):\n    """Show installed games for console, staff picks one\."""[\s\S]*?return SALE_GAME_SELECT'

# Find all matches
matches = list(re.finditer(pattern1, content))
if len(matches) >= 2:
    # The SECOND one is the game-select (we want the first one - that's the original)
    # Actually, let me check both
    print(f"Found {len(matches)} matches for game-select prompt_mins")
    # Remove the second one (which is the game-select version)
    for m in matches:
        print(f"  Match at pos {m.start()}: ...{content[m.start():m.start()+50]}...")
    
    # Keep first, remove second
    cut_start = matches[1].start()
    cut_end = matches[1].end()
    # Cut from the blank line before async def to the end of return SALE_GAME_SELECT
    if cut_start > 0 and content[cut_start-1] == '\n':
        cut_start -= 1
    
    # Find the end - next function definition or blank line
    after = content[cut_end:]
    # The step_game_select should come right after
    step_match = re.search(r'\n\nasync def step_game_select\(', after)
    if step_match:
        # Remove step_game_select too
        step_end = step_match.start() + cut_end
        
        # Find where step_game_select ends (next async def or end of blank line before next decorator)
        remaining = after[step_match.start():]
        next_func = re.search(r'\n\n@log_duration|$', remaining[50:])  # skip past function body
        if next_func:
            step_end = cut_end + step_match.start() + next_func.start() + 50
        
        content = content[:cut_start] + content[step_end:]
        print(f"Removed game-select prompt_mins + step_game_select (positions {cut_start} to {step_end})")
    else:
        content = content[:cut_start] + content[cut_end:]
        print(f"Removed game-select prompt_mins only (positions {cut_start} to {cut_end})")
else:
    print(f"WARNING: Expected 2 prompt_mins, found {len(matches)}")

# ── Fix 2: Fix the step_console normalization ──
old_check = """    if text not in VALID_CONSOLES:
        await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ keyboard မှ Console ID ရွေးပါ -")
        return await prompt_console(update, context)

    context.user_data["c_id"] = text
    return await _check_console_in_session(update, context, text)"""

new_check = """    # Normalize: remove spaces so "C - 09" matches "C-09"
    normalized = text.replace(" ", "")
    if normalized not in VALID_CONSOLES:
        await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ keyboard မှ Console ID ရွေးပါ -")
        return await prompt_console(update, context)

    context.user_data["c_id"] = normalized
    return await _check_console_in_session(update, context, normalized)"""

count = content.count(old_check)
print(f"Fix 2 matches: {count}")
if count > 0:
    content = content.replace(old_check, new_check, 1)
else:
    print("WARNING: Fix 2 pattern not found!")

with open(target, 'w') as f:
    f.write(content)

print(f"Written to {target}")
print(f"File size: {len(content)} bytes")
