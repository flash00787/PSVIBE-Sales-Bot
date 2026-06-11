"""Fix misplaced attendance handler entries in app.py"""

with open('/root/psvibe-sales-bot/bot/app.py', 'r') as f:
    content = f.read()

# Remove the wrongly placed attendance handler lines
wrong_section = '''        ("checkin",      cmd_checkin),
        ("checkout",     cmd_checkout),
        ("attendance",   cmd_attendance),
        ("salary",       cmd_salary),
        ("staff_status", cmd_staff_status),
        ("staff_list",   cmd_staff_list),
'''

if wrong_section in content:
    content = content.replace(wrong_section, '', 1)
    
    # Find the correct insertion point: after the LAST "newbooking" in the tuple list
    # The tuple list is the one that ends with "]:\n        app.add_handler(CommandHandler(cmd, fn))"
    target_marker = '''        ("newbooking",     cmd_staff_booking),
        ("cancelbooking",  cmd_cancel_booking),
    ]:'''
    
    insertion_block = '''        ("checkin",      cmd_checkin),
        ("checkout",     cmd_checkout),
        ("attendance",   cmd_attendance),
        ("salary",       cmd_salary),
        ("staff_status", cmd_staff_status),
        ("staff_list",   cmd_staff_list),
        ("cancelbooking",  cmd_cancel_booking),
    ]:'''
    
    content = content.replace(target_marker, insertion_block)
    
    with open('/root/psvibe-sales-bot/bot/app.py', 'w') as f:
        f.write(content)
    print('SUCCESS: Attendance handlers moved to correct tuple list')
else:
    print('WARNING: Wrong section not found. Checking current state...')
    with open('/root/psvibe-sales-bot/bot/app.py', 'r') as f:
        for i, line in enumerate(f.readlines(), 1):
            if 'checkin' in line and 'BotCommand' not in line and 'cb_checkin' not in line:
                print(f'  Line {i}: {line.rstrip()}')
