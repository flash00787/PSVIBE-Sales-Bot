#!/usr/bin/env python3
"""Phase 4: Fix bot handlers"""
import re

# ─── 4b: api_client.py ───────────────────────────────────────────
with open('/root/psvibe-sales-bot/bot/api_client.py') as f:
    content = f.read()

# Add move_console_game before the last line
move_fns = '''
def move_console_game(from_console, game_title, to_console):
    """Move a game between console/SSD locations via API."""
    result = _api_call("POST", "move_console_game", json_data={
        "game_title": game_title,
        "from_console": from_console,
        "to_console": to_console,
    })
    return result is not None and result.get("success", False)


async def move_console_game_async(from_console, game_title, to_console):
    """Async: Move a game between console/SSD locations via API."""
    return await _api_call_async("POST", "move_console_game", json_data={
        "game_title": game_title,
        "from_console": from_console,
        "to_console": to_console,
    })
'''

# Add before topup helper functions at the end
insert_pt = content.rfind('\n\nasync def api_add_topup_async')
if insert_pt == -1:
    insert_pt = content.rfind('\n\nasync def api_add_sales_record_async')
if insert_pt == -1:
    print("4b: WARNING - could not find insertion point, appending")
    content += '\n' + move_fns
else:
    content = content[:insert_pt] + '\n' + move_fns + '\n' + content[insert_pt:]

with open('/root/psvibe-sales-bot/bot/api_client.py', 'w') as f:
    f.write(content)
print('4b: api_client.py updated')

# ─── 4c: games.py ────────────────────────────────────────────────
with open('/root/psvibe-sales-bot/bot/handlers/games.py') as f:
    content = f.read()

# In _show_game_detail: change status checks
# Old: if status == "Installed": cons_list.append(cid)
# Old: elif status == "SSD Copy": ssd_list.append(...)
# Old: elif status == "Session": ssd_list.append(...)
# Change cons_list to include "Moved", and ssd_list to include "Moved"

# Fix in _show_game_detail
old_check1 = '                if status == "Installed":\n                    cons_list.append(cid)\n                elif status == "SSD Copy":\n                    ssd_list.append(f"{cid} ({status})")\n                elif status == "Session":\n                    ssd_list.append(f"{cid} (Session)")\n                # Skip entries with status "false" (not installed)'
new_check1 = '                if status == "Installed":\n                    cons_list.append(cid)\n                elif status in ("SSD Copy", "Moved"):\n                    ssd_list.append(f"{cid} ({status})")\n                elif status == "Session":\n                    ssd_list.append(f"{cid} (Session)")\n                # Skip entries with status "Not Installed"'
if old_check1 in content:
    content = content.replace(old_check1, new_check1)
    print('4c: _show_game_detail checks fixed')
else:
    print('4c: _show_game_detail pattern NOT FOUND')

# Fix in step_game_detail_pick (same pattern)
if old_check1 in content:
    content = content.replace(old_check1, new_check1)
    print('4c: step_game_detail_pick checks fixed')
else:
    print('4c: step_game_detail_pick - already fixed or pattern not found')

with open('/root/psvibe-sales-bot/bot/handlers/games.py', 'w') as f:
    f.write(content)
print('4c: games.py updated')

# ─── 4d: __init__.py - Add new states and buttons ─────────────────
with open('/root/psvibe-sales-bot/bot/__init__.py') as f:
    content = f.read()

# Find BotState class and add new states after SSD_RET_GAME = 97
old_ssd_states = '    SSD_RET_GAME = 97\n    DISC_SELECT = 98'
new_ssd_states = '    SSD_RET_GAME = 97\n    SSD_MOVE_SSD = 42\n    SSD_MOVE_GAME = 43\n    SSD_MOVE_CONS = 44\n    SSD_MOVE_FROM_CONS = 45\n    SSD_MOVE_FROM_GAME = 46\n    SSD_MOVE_TO_SSD = 47\n    DISC_SELECT = 98'
if old_ssd_states in content:
    content = content.replace(old_ssd_states, new_ssd_states)
    print('4d: BotState new states added')
else:
    print('4d: BotState pattern NOT FOUND')

# Add the module-level constants after the existing SSD_RET_GAME assignment
old_ssd_ret = 'SSD_RET_GAME = BotState.SSD_RET_GAME\nDISC_SELECT = BotState.DISC_SELECT'
new_ssd_ret = 'SSD_RET_GAME = BotState.SSD_RET_GAME\nSSD_MOVE_SSD = BotState.SSD_MOVE_SSD\nSSD_MOVE_GAME = BotState.SSD_MOVE_GAME\nSSD_MOVE_CONS = BotState.SSD_MOVE_CONS\nSSD_MOVE_FROM_CONS = BotState.SSD_MOVE_FROM_CONS\nSSD_MOVE_FROM_GAME = BotState.SSD_MOVE_FROM_GAME\nSSD_MOVE_TO_SSD = BotState.SSD_MOVE_TO_SSD\nDISC_SELECT = BotState.DISC_SELECT'
if old_ssd_ret in content:
    content = content.replace(old_ssd_ret, new_ssd_ret)
    print('4d: module-level constants added')
else:
    print('4d: module-level pattern NOT FOUND')

# Add BTN_SSD_MOVE buttons after BTN_SSD_RETURN
old_ssd_btns = "BTN_SSD_RETURN   = '\\u21a9\\ufe0f Console \\u2192 SSD (Return)'"
new_ssd_btns = "BTN_SSD_RETURN   = '\\u21a9\\ufe0f Console \\u2192 SSD (Return)'\nBTN_SSD_MOVE_TO_CONSOLE = '\\U0001f504 SSD\\u2192Console'\nBTN_SSD_MOVE_TO_SSD = '\\U0001f504 Console\\u2192SSD'"
if old_ssd_btns in content:
    content = content.replace(old_ssd_btns, new_ssd_btns)
    print('4d: BTN_SSD_MOVE buttons added')
else:
    print('4d: BTN_SSD buttons pattern NOT FOUND')

# Add new states to __all__ exports list
# Find the SSD states in __all__
old_export_ssd = "'SSD_RET_CONS', 'SSD_RET_GAME', 'DISC_SELECT'"
new_export_ssd = "'SSD_RET_CONS', 'SSD_RET_GAME', 'SSD_MOVE_SSD', 'SSD_MOVE_GAME', 'SSD_MOVE_CONS', 'SSD_MOVE_FROM_CONS', 'SSD_MOVE_FROM_GAME', 'SSD_MOVE_TO_SSD', 'DISC_SELECT'"
if old_export_ssd in content:
    content = content.replace(old_export_ssd, new_export_ssd)
    print('4d: __all__ exports updated')
else:
    print('4d: __all__ export pattern NOT FOUND')

# Add new BTN exports to __all__
old_export_btn = "'BTN_SSD_RETURN',"
new_export_btn = "'BTN_SSD_RETURN', 'BTN_SSD_MOVE_TO_CONSOLE', 'BTN_SSD_MOVE_TO_SSD',"
if old_export_btn in content:
    content = content.replace(old_export_btn, new_export_btn)
    print('4d: BTN exports added to __all__')
else:
    print('4d: BTN export pattern NOT FOUND')

with open('/root/psvibe-sales-bot/bot/__init__.py', 'w') as f:
    f.write(content)
print('4d: __init__.py updated')

print('\nPhase 4 code edits complete.')
