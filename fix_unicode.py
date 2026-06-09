#!/usr/bin/env python3
"""Fix mangled unicode escapes in ssd_disc.py"""
with open("/root/psvibe-sales-bot/bot/handlers/ssd_disc.py") as f:
    content = f.read()

# Fix the mangled lines - they lost their backslash-escapes and quotes
content = content.replace(
    '            U0001f504 *SSDu2192Console Move*nnSSD u101bu103du1031u1038u1015u102b:,\n            parse_mode=Markdown,',
    '            "\U0001f504 *SSD\u2192Console Move*\n\nSSD \u101b\u103d\u1031\u1038\u1015\u102b:",\n            parse_mode="Markdown",'
)

content = content.replace(
    '            U0001f504 *Consoleu2192SSD Move*nnConsole u101bu103du1031u1038u1015u102b:,\n            parse_mode=Markdown,',
    '            "\U0001f504 *Console\u2192SSD Move*\n\nConsole \u101b\u103d\u1031\u1038\u1015\u102b:",\n            parse_mode="Markdown",'
)

# Also fix any mangled lines in the move handler functions at the end
content = content.replace(
    '        await update.message.reply_text(\n            f"\\U0001f4c0 <b>{SSD_NAMES[ssd_id]}</b> \\u2014',
    '        await update.message.reply_text(\n            f"\U0001f4c0 <b>{SSD_NAMES[ssd_id]}</b> \u2014'
)

with open("/root/psvibe-sales-bot/bot/handlers/ssd_disc.py", "w") as f:
    f.write(content)
print("fixed")
