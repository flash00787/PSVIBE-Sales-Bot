"""Register attendance command handlers in app.py"""
f = open('/root/psvibe-sales-bot/bot/app.py', 'r')
content = f.read()
f.close()

lines = content.split('\n')
new_lines = []
handler_added = False
botcmd_added = False

att_handlers = [
    '        ("checkin",      cmd_checkin),',
    '        ("checkout",     cmd_checkout),',
    '        ("attendance",   cmd_attendance),',
    '        ("salary",       cmd_salary),',
    '        ("staff_status", cmd_staff_status),',
    '        ("staff_list",   cmd_staff_list),',
]

att_botcmds = [
    '            BotCommand("checkin",     "\u2705 Staff Check-in"),',
    '            BotCommand("checkout",    "\u274c Staff Check-out"),',
    '            BotCommand("attendance",  "\U0001f4cb Daily Attendance"),',
    '            BotCommand("salary",      "\U0001f4b0 Staff Salary"),',
    '            BotCommand("staff_status","\U0001f465 Staff Status"),',
    '            BotCommand("staff_list",  "\U0001f4dd Staff List"),',
]

for line in lines:
    new_lines.append(line)
    # After "newbooking" handler registration
    if '"newbooking"' in line and 'cmd_staff_booking' in line and not handler_added:
        for h in att_handlers:
            new_lines.append(h)
        handler_added = True
    # After "freport" BotCommand
    if '"freport"' in line and not botcmd_added:
        for b in att_botcmds:
            new_lines.append(b)
        botcmd_added = True

content = '\n'.join(new_lines)
f = open('/root/psvibe-sales-bot/bot/app.py', 'w')
f.write(content)
f.close()
print(f"Handlers added: {handler_added}")
print(f"BotCommands added: {botcmd_added}")
