#!/usr/bin/env python3
"""Fix step_sbk_dur to do avail check and show console selection."""
import sys

with open('/root/psvibe-sales-bot/bot/handlers/booking.py', 'r') as f:
    text = f.read()

func_start = text.find('async def step_sbk_dur')
func_end = text.find('async def step_sbk_game', func_start)

if func_start < 0 or func_end < 0:
    print("ERROR: Functions not found")
    sys.exit(1)

old_func = text[func_start:func_end]

new_func = (
    'async def step_sbk_dur(update: Update, context: ContextTypes.DEFAULT_TYPE):\n'
    '    """Handle time slot -> check avail and show console selection."""\n'
    '    text = update.message.text.strip()\n'
    '    if text == BTN_CANCEL:\n'
    '        return await cmd_cancel(update, context)\n'
    '    if text == BTN_BACK:\n'
    '        today    = now_mmt().date()\n'
    '        tomorrow = today + timedelta(days=1)\n'
    '        d2       = today + timedelta(days=2)\n'
    '        def dfmt(d): return d.strftime("%-m/%-d/%Y")\n'
    '        kb = [\n'
    '            [dfmt(today) + " (\u101a\u1014\u1031\u102c)", dfmt(tomorrow) + " (\u1019\u1014\u1014\u103a\u1000\u103c\u1031\u102c)"],\n'
    '            [dfmt(d2)],\n'
    '            [BTN_SBK_CUSTOM],\n'
    '            [BTN_BACK, BTN_CANCEL],\n'
    '        ]\n'
    '        await update.message.reply_text(\n'
    '            "\u1045 Booking Date \u101e\u103d\u1031\u1038\u1015\u102b\u1038:",\n'
    '            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),\n'
    '        )\n'
    '        return SBK_TIME\n'
    '\n'
    '    import re as _re2\n'
    '    if not _re2.match(r"^\\d{1,2}:\\d{2}$", text):\n'
    '        await update.message.reply_text("\u26a0\ufe0f Time format: HH:MM  (\u1019\u102c\u101e\u1019\u102c: 14:30)")\n'
    '        return SBK_DUR\n'
    '\n'
    '    context.user_data["sbk_time"] = text\n'
    '\n'
    '    rows = await _sbk_console_kb()\n'
    '    if rows and len(rows) > 1:\n'
    '        await update.message.reply_text(\n'
    '            "\u2705 Available Consoles:\\n\\nConsole ID \u101e\u103d\u1031\u1038\u1015\u102b\u1038:",\n'
    '            reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True),\n'
    '        )\n'
    '    else:\n'
    '        await update.message.reply_text(\n'
    '            "\u26a0\ufe0f Free console \u1019\u101b\u103e\u102d\u1015\u102b\\n\u1014\u1031\u1037\u101b\u1014\u1031\u1038\u1001\u103c\u101e\u101a\u1039\u101e\u103d\u1031\u1038\u1015\u102b\u1038:",\n'
    '            reply_markup=ReplyKeyboardMarkup([[BTN_BACK, BTN_CANCEL]], resize_keyboard=True),\n'
    '        )\n'
    '    return SBK_CONSOLE\n'
)

text = text[:func_start] + new_func + text[func_end:]

with open('/root/psvibe-sales-bot/bot/handlers/booking.py', 'w') as f:
    f.write(text)

print("Done! step_sbk_dur rewritten with avail check -> SBK_CONSOLE")

# Verify
with open('/root/psvibe-sales-bot/bot/handlers/booking.py', 'r') as f:
    v = f.read()

idx = v.find('async def step_sbk_dur')
end = v.find('async def step_sbk_game', idx)
fragment = v[idx:end]
assert 'SBK_CONSOLE' in fragment, "FAIL: SBK_CONSOLE not found"
assert 'avail' in fragment, "FAIL: avail not found"
print("Verified OK")
print(fragment)
