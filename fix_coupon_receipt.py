#!/usr/bin/env python3
"""Fix: Add coupon capture + display to sales.py receipt."""

with open("/root/psvibe-sales-bot/bot/handlers/sales.py", "r") as f:
    c = f.read()

# 1. Add coupon capture BEFORE context.user_data.clear()
clear_marker = "    context.user_data.clear()\n"
capture = (
    '    # Capture coupon vars before clear\n'
    '    coupon_code = d.get("_cashback_coupon", "")\n'
    '    coupon_mins = d.get("_cashback_coupon_mins", 0)\n\n'
)

# Find the clear() call
clear_idx = c.find(clear_marker)
if clear_idx < 0:
    print("FAIL: context.user_data.clear() not found")
    exit(1)
c = c[:clear_idx] + capture + c[clear_idx:]

# 2. Add coupon line to receipt
# Find where wallet_bal_line is used in the receipt
wallet_line_marker = 'f"{wallet_bal_line}"'
wl_idx = c.find(wallet_line_marker)
if wl_idx < 0:
    print("FAIL: wallet_bal_line in receipt not found")
    exit(1)

# Replace: f"{wallet_bal_line}"  with  f"{coupon_line}\\n{wallet_bal_line}" if coupon_code else f"{wallet_bal_line}"
old = c[wl_idx:wl_idx+len(wallet_line_marker)]
new = ('f"{coupon_line}\\n{wallet_bal_line}" if coupon_code else f"{wallet_bal_line}"')
c = c.replace(old, new, 1)

# 3. Add coupon_line variable definition before the receipt
# Find where receipt line starts
rcpt_marker = 'await update.message.reply_text(\n'
rcpt_idx = c.find(rcpt_marker)
if rcpt_idx < 0:
    print("FAIL: receipt marker not found")
    exit(1)

# Insert coupon_line variable after receipt_kb declaration
# Find the line before the reply_text call
coupon_var = (
    '    coupon_line = f"🎫 *CashBack Coupon:* {coupon_code} — *{coupon_mins} mins*" if coupon_code else ""\n'
    '    if coupon_code:\n'
    '        await update.message.reply_text(\n'
    '            f"🎫 *100% CashBack Coupon!*\\n"\n'
    '            f"Code: `{coupon_code}`\\n"\n'
    '            f"Minutes: *{coupon_mins} mins*\\n"\n'
    '            f"\\u23f0 နောက်လာရင် ဒီ code ကို ပြပြီး ပြန်ဆော့လို့ရပါတယ်!",\n'
    '            parse_mode="Markdown",\n'
    '        )\n\n'
)

# Insert after receipt_kb check
kb_check = 'if receipt_kb:\n        await update.message.reply_text'
kb_idx = c.find(kb_check)
if kb_idx < 0:
    print("FAIL: receipt_kb check not found")
    exit(1)

# Find end of that block - look for empty line or next section
end_of_kb = c.find("\n\n    # ── SHEET WRITES", kb_idx)
if end_of_kb < 0:
    print("FAIL: end of kb block not found")
    exit(1)

# Insert coupon_var right after the receipt_kb block
c = c[:end_of_kb] + "\n" + coupon_var + c[end_of_kb:]

with open("/root/psvibe-sales-bot/bot/handlers/sales.py", "w") as f:
    f.write(c)
print("SUCCESS: Coupon receipt display added!")
