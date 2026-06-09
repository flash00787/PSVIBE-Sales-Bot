#!/usr/bin/env python3
"""Fix step_console in sales.py to normalize console IDs."""
import re
import sys

filepath = sys.argv[1]
with open(filepath, 'r') as f:
    content = f.read()

# 1. Add normalization before VALID_CONSOLES check
old_check = """    if text not in VALID_CONSOLES:
        await update.message.reply_text("\u26a0\ufe0f \u1000\u103b\u1031\u1038\u101c\u103a\u1015\u103c\u1031\u1038\u101e\u1019\u1039 keyboard \u1019\u103a Console ID \u101b\u103d\u1035\u1038\u1015\u102b -")
        return await prompt_console(update, context)"""

new_check = """    # Normalize: remove spaces so "C - 09" matches "C-09"
    normalized = text.replace(" ", "")
    if normalized not in VALID_CONSOLES:
        await update.message.reply_text("\u26a0\ufe0f \u1000\u103b\u1031\u1038\u101c\u103a\u1015\u103c\u1031\u1038\u101e\u1019\u1039 keyboard \u1019\u103a Console ID \u101b\u103d\u1035\u1038\u1015\u102b -")
        return await prompt_console(update, context)"""

count1 = content.count(old_check)
print(f"Found old_check: {count1}")

if count1 > 0:
    content = content.replace(old_check, new_check, 1)

# 2. Replace c_id assignment to use normalized
content = content.replace(
    '    context.user_data["c_id"] = text\n    return await _check_console_in_session(update, context, text)',
    '    context.user_data["c_id"] = normalized\n    return await _check_console_in_session(update, context, normalized)',
    1
)

with open(filepath, 'w') as f:
    f.write(content)

print("Done!")
