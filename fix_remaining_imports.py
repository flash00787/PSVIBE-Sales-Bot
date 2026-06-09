# Fix admin_bookings.py, broadcast.py, commands.py, console_mgmt.py, 
# discount.py, games.py, ginst.py, notify.py, referral.py, ssd_disc.py, waitlist.py
import os

base = '/root/Sales-Tele-Bot_refactored/bot/handlers'
files_to_fix = [
    'admin_bookings.py', 'broadcast.py', 'commands.py', 'console_mgmt.py',
    'discount.py', 'games.py', 'ginst.py', 'notify.py', 'referral.py',
    'ssd_disc.py', 'waitlist.py'
]

for fname in files_to_fix:
    fpath = os.path.join(base, fname)
    with open(fpath) as f:
        lines = f.readlines()
    
    # Check if already has from bot.handlers import *
    has_import = any('from bot.handlers import *' in line for line in lines)
    
    if not has_import:
        # Find first non-blank, non-docstring, non-comment line
        insert_at = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('"') and not stripped.startswith("'"):
                insert_at = i
                break
        
        if insert_at > 0 and not lines[insert_at].strip().startswith('from '):
            # Insert before the first actual code line
            lines.insert(insert_at, 'from bot.handlers import *\n')
            with open(fpath, 'w') as f:
                f.writelines(lines)
            print(f'{fname}: added import at line {insert_at+1}')
        else:
            print(f'{fname}: first code line is already import (line {insert_at+1}: {lines[insert_at].strip()})')
    else:
        print(f'{fname}: already has import')

print('DONE')
