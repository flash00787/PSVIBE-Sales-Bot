#!/usr/bin/env python3
"""Add game selection step to sales flow."""
import sys

filepath = sys.argv[1]

with open(filepath, 'r') as f:
    content = f.read()

# 1. Add import for get_games_on_console_async and SALE_GAME_SELECT
# Check if already added
if 'get_games_on_console_async' not in content:
    content = content.replace(
        'fetch_console_multiplier_async,',
        'fetch_console_multiplier_async,\n    get_games_on_console_async,'
    )
    print("1a. Added get_games_on_console_async import")

if 'SALE_GAME_SELECT' not in content:
    content = content.replace(
        'SALE_CONFIRM, SESSION_SHORTFALL',
        'SALE_CONFIRM,\n    SALE_GAME_SELECT, SESSION_SHORTFALL'
    )
    print("1b. Added SALE_GAME_SELECT import")

# 2. Modify _check_console_in_session: route to prompt_game_select
# There are two places: main return and except return
old1 = '        return await prompt_mins(update, context)'
new1 = '        return await prompt_game_select(update, context)'

if old1 in content:
    # Replace only the non-except occurrences? No, replace both
    content = content.replace(old1, new1)
    print("2. Modified _check_console_in_session routes to prompt_game_select")
else:
    print("2. WARNING: prompt_mins not found in _check_console_in_session?")

# 3. Add prompt_game_select and step_game_select before step_ds_console_in_session
insert_marker = '@log_duration("sales:step_ds_console_in_session")\nasync def step_ds_console_in_session'
if insert_marker in content:
    new_funcs = '''
async def prompt_game_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show installed games for console, staff picks one."""
    cid = context.user_data.get("c_id", "")
    if not cid:
        return await prompt_mins(update, context)
    try:
        games = await get_games_on_console_async(cid)
    except Exception as e:
        logging.warning("prompt_game_select: %s", e)
        games = []
    if not games:
        return await prompt_mins(update, context)
    kb = [[g] for g in games]
    kb.append(["\\u23ed Skip Game"])
    kb.append(["\\u2b05 Back"])
    await update.message.reply_text(
        f"\\U0001f3ae <b>{cid}</b> \\u1019\\u103a\\u101b Install \\u101c\\u1031\\u1015\\u1039\\u1015\\u1010\\u1031\\u1038 \\u1002\\u102d\\u1019\\u103a\\u1038\\u1010\\u1031\\u1038\\n"
        f"\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\n"
        f"\\u1006\\u1031\\u102c\\u1004\\u1039\\u1019\\u102d\\u1014\\u1039 \\u1002\\u102d\\u1019\\u103a\\u1038\\u1000\\u103b\\u1031\\u102c \\u101b\\u103d\\u1031\\u1038\\u1015\\u1031\\u102b\\u103a:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SALE_GAME_SELECT

async def step_game_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store selected game and proceed to mins."""
    text = update.message.text.strip()
    if text == "\\u2b05 Back":
        context.user_data.pop("c_id", None)
        return await prompt_console(update, context)
    if text == "\\u23ed Skip Game":
        context.user_data["game_title"] = ""
    else:
        context.user_data["game_title"] = text
    return await prompt_mins(update, context)

'''
    content = content.replace(insert_marker, new_funcs + '\n' + insert_marker)
    print("3. Added prompt_game_select and step_game_select")
else:
    print("3. WARNING: Could not find insertion point")

with open(filepath, 'w') as f:
    f.write(content)

print("Done!")
