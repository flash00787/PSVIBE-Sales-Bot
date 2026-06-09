#!/usr/bin/env python3
"""Update bot app.py with new SSD Move state handlers"""

with open('/root/psvibe-sales-bot/bot/app.py') as f:
    content = f.read()

# Add imports for the new states
old_app_import = '    SSD_RET_GAME, SSD_XFER_CONS, SSD_XFER_GAME, SSD_XFER_SSD, STOCK_ITEM,'
new_app_import = '    SSD_RET_GAME, SSD_XFER_CONS, SSD_XFER_GAME, SSD_XFER_SSD,\n    SSD_MOVE_SSD, SSD_MOVE_GAME, SSD_MOVE_CONS, SSD_MOVE_FROM_CONS,\n    SSD_MOVE_FROM_GAME, SSD_MOVE_TO_SSD, STOCK_ITEM,'

if old_app_import in content:
    content = content.replace(old_app_import, new_app_import)
    print('app.py: imports updated')
else:
    print('app.py: import pattern NOT FOUND')

# Add state entries after SSD_RET_GAME in the states dict
old_ssd_ret_state = '            SSD_RET_GAME:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_ret_game)],'
new_ssd_ret_state = '''            SSD_RET_GAME:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_ret_game)],
            # ── SSD Move flows ──
            SSD_MOVE_SSD:      [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_move_ssd)],
            SSD_MOVE_GAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_move_game)],
            SSD_MOVE_CONS:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_move_cons)],
            SSD_MOVE_FROM_CONS:[MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_move_from_cons)],
            SSD_MOVE_FROM_GAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_move_from_game)],
            SSD_MOVE_TO_SSD:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_move_to_ssd)],'''

if old_ssd_ret_state in content:
    content = content.replace(old_ssd_ret_state, new_ssd_ret_state)
    print('app.py: state handlers added')
else:
    print('app.py: SSD_RET_GAME state pattern NOT FOUND')

with open('/root/psvibe-sales-bot/bot/app.py', 'w') as f:
    f.write(content)
print('bot/app.py updated')
