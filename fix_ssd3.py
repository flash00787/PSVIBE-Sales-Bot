#!/usr/bin/env python3
"""Fix ssd_disc.py - replace mangled lines with correct ones"""

with open("/root/psvibe-sales-bot/bot/handlers/ssd_disc.py") as f:
    lines = f.readlines()

# Find and fix the mangled blocks
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    # Detect mangled block: starts with "    if text == BTN_SSD_MOVE_TO_CONSOLE:"
    if 'BTN_SSD_MOVE_TO_CONSOLE' in line:
        new_lines.append(line)  # keep the if line
        i += 1
        # Skip mangled lines until we find "        return SSD_MOVE_SSD"
        while i < len(lines) and 'return SSD_MOVE_SSD' not in lines[i]:
            i += 1
        # Insert correct lines
        new_lines.append('        await update.message.reply_text(\n')
        new_lines.append('            "\U0001f504 *SSD\u2192Console Move*\n\nSSD \u101b\u103d\u1031\u1038\u1015\u102b:",\n')
        new_lines.append('            parse_mode="Markdown",\n')
        new_lines.append('            reply_markup=_ssd_kb(),\n')
        new_lines.append('        )\n')
        new_lines.append(lines[i])  # return SSD_MOVE_SSD
        i += 1
    elif 'BTN_SSD_MOVE_TO_SSD' in line:
        new_lines.append(line)  # keep the if line
        i += 1
        # Skip mangled lines until we find "        return SSD_MOVE_FROM_CONS"
        while i < len(lines) and 'return SSD_MOVE_FROM_CONS' not in lines[i]:
            i += 1
        # Insert correct lines
        new_lines.append('        await update.message.reply_text(\n')
        new_lines.append('            "\U0001f504 *Console\u2192SSD Move*\n\nConsole \u101b\u103d\u1031\u1038\u1015\u102b:",\n')
        new_lines.append('            parse_mode="Markdown",\n')
        new_lines.append('            reply_markup=ReplyKeyboardMarkup(\n')
        new_lines.append('                [[c["id"]] for c in get_consoles_from_setting()] + [[BTN_BACK]],\n')
        new_lines.append('                resize_keyboard=True,\n')
        new_lines.append('            ),\n')
        new_lines.append('        )\n')
        new_lines.append(lines[i])  # return SSD_MOVE_FROM_CONS
        i += 1
    else:
        new_lines.append(line)
        i += 1

# Also fix mangled text in the move handler functions at the bottom
# The added handlers might have similar issues
fixed = ''.join(new_lines)
# Fix any remaining mangled patterns in handler functions
fixed = fixed.replace('\\u101b\\u103d\\u1031\\u1038\\u1015\\u102b', '\u101b\u103d\u1031\u1038\u1015\u102b')
fixed = fixed.replace('\\U0001f504', '\U0001f504')
fixed = fixed.replace('\\U0001f4c0', '\U0001f4c0')
fixed = fixed.replace('\\u2192', '\u2192')
fixed = fixed.replace('\\u2705', '\u2705')
fixed = fixed.replace('\\u274c', '\u274c')
fixed = fixed.replace('\\u26a0\\ufe0f', '\u26a0\ufe0f')
fixed = fixed.replace('\\u2014', '\u2014')
fixed = fixed.replace('\\U0001f579\\ufe0f', '\U0001f579\ufe0f')

with open("/root/psvibe-sales-bot/bot/handlers/ssd_disc.py", "w") as f:
    f.write(fixed)
print("fixed")
