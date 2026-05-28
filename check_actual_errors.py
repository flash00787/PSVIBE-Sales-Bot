# Get actual bot.log errors from V.2 run
import subprocess
import os

bot_log = '/root/Sales-Tele-Bot_refactored/logs/bot.log'
if os.path.exists(bot_log):
    with open(bot_log) as f:
        # Read last 100 lines
        lines = f.readlines()
        last_100 = lines[-100:]
    
    print(f'=== Last {len(last_100)} lines of bot.log ===')
    for line in last_100:
        stripped = line.rstrip()
        if any(kw in stripped.upper() for kw in ['ERROR', 'EXCEPTION', 'TRACEBACK', 'NAMEERROR', 'FAIL', 'IMPORTERROR']):
            print(f'⚠️  {stripped}')
        else:
            print(f'   {stripped}')
else:
    print('bot.log not found')
    # Try alternative paths
    for p in ['/root/Sales-Tele-Bot_refactored/logs/bot_status.log', '/root/Sales-Tele-Bot_refactored/bot_status.log']:
        if os.path.exists(p):
            print(f'\nFound: {p}')
            with open(p) as f:
                lines = f.readlines()
                last_50 = lines[-50:]
            for line in last_50:
                print(line.rstrip())
