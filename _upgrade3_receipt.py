#!/usr/bin/env python3
"""Upgrade 3: Auto Receipt Generator - modify members.py"""
import re, sys

with open('/root/psvibe-sales-bot/bot/handlers/members.py', 'r') as f:
    content = f.read()

changes = 0

# 1. Add STAFF_NOTIFY_CHAT to imports from bot
old_import = "    now_mmt, rank_emoji, save_receipt_json, show_main_menu, step_hdr,"
new_import = "    now_mmt, rank_emoji, save_receipt_json, show_main_menu, STAFF_NOTIFY_CHAT, step_hdr,"
if old_import in content:
    content = content.replace(old_import, new_import)
    print("+ Added STAFF_NOTIFY_CHAT to imports")
    changes += 1
else:
    print("ERROR: Could not find import line to modify")
    sys.exit(1)

# 2. Add auto_generate_receipt function
auto_receipt_func = '''

async def auto_generate_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE, tu_vid: str, receipt_data: dict):
    """Auto-send formatted receipt to staff Telegram chat after topup completion."""
    try:
        staff_chat_id = STAFF_NOTIFY_CHAT
        if not staff_chat_id:
            logging.warning("auto_receipt: STAFF_NOTIFY_CHAT not configured, skipping")
            return
        
        try:
            chat_id = int(staff_chat_id)
        except ValueError:
            chat_id = staff_chat_id
        
        shop_name = "PS VIBE Gaming Center"
        
        rd = receipt_data
        kpay = rd.get("kpay", 0) or 0
        cash = rd.get("cash", 0) or 0
        total_paid = kpay + cash
        
        lines = [
            f"\\U0001f9fe *{shop_name}*",
            f"\\U0001f4c4 *Top-Up Receipt*",
            f"\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501",
            f"\\U0001f4aa *Voucher:* `{tu_vid}`",
            f"\\U0001f464 *Member:* `{rd.get('member_id', 'N/A')}`",
            f"\\U0001f3d6 *Rank:* {rd.get('rank', 'N/A')}",
            f"\\U0001f4c5 *Date:* {rd.get('date', 'N/A')}",
            f"\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501",
            f"\\U0001f4b0 *Amount:* {rd.get('amount', 0):,} Ks",
            f"\\u23f3 *Base Mins:* {rd.get('base_mins', 0):,}",
            f"\\U0001f381 *Bonus Mins:* +{rd.get('bonus_mins', 0):,}",
            f"\\U0001f525 *Total Mins:* {rd.get('total_mins', 0):,}",
            f"\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501",
            f"\\U0001f4b3 *KPay:* {kpay:,} Ks",
            f"\\U0001f4b5 *Cash:* {cash:,} Ks",
            f"\\U0001f4b2 *Total Paid:* {total_paid:,} Ks",
            f"\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501\\u2501",
            f"\\U0001f4ca *Balance Before:* {rd.get('prev_balance', 0):,} mins",
            f"\\U0001f4c8 *Balance After:* {rd.get('balance_after', 0):,} mins",
            f"\\U0001f4de *Phone:* {rd.get('phone', '-')}",
        ]
        
        msg = "\\n".join(lines)
        await context.bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode="Markdown",
        )
        logging.info("auto_receipt: sent receipt %s to staff chat %s", tu_vid, staff_chat_id)
    except Exception as e:
        logging.error("auto_receipt: failed to send receipt %s: %s", tu_vid, e, exc_info=True)
'''

# Insert before _fmt_other_payments
marker = '\ndef _fmt_other_payments('
if marker in content:
    content = content.replace(marker, auto_receipt_func + marker)
    print("+ Added auto_generate_receipt function")
    changes += 1
else:
    print("ERROR: Could not find _fmt_other_payments insertion point")
    # Show context
    for i, line in enumerate(content.split('\n')):
        if '_fmt_other_payments' in line:
            print(f"  Found at line {i+1}: {line.strip()}")
    sys.exit(1)

# 3. Call auto_generate_receipt after get_receipt_kb in step_tu_confirm
old_pattern = "    receipt_kb = get_receipt_kb(tu_vid)\n    context.user_data.clear()"
replacement = '''    receipt_kb = get_receipt_kb(tu_vid)

    # Auto-send receipt to staff Telegram chat
    receipt_data = {
        "type": "topup", "voucher_id": tu_vid, "date": today,
        "member_id": tu_id, "rank": r_saved, "amount": tu_amt,
        "base_mins": tu_base, "bonus_mins": tu_bonus, "total_mins": tu_mins,
        "kpay": tu_kpay, "cash": tu_cash, "phone": tu_phone,
        "balance_mins": bal_mins, "prev_balance": prev_bal,
        "balance_change": tu_mins, "balance_after": bal_mins,
    }
    asyncio.create_task(auto_generate_receipt(update, context, tu_vid, receipt_data))

    context.user_data.clear()'''

if old_pattern in content:
    content = content.replace(old_pattern, replacement)
    print("+ Added auto_generate_receipt call in step_tu_confirm")
    changes += 1
else:
    print("WARNING: Could not find exact pattern. Trying flexible match...")
    lines = content.split('\n')
    new_lines = []
    i = 0
    found = False
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        if 'get_receipt_kb(tu_vid)' in line and i+1 < len(lines) and 'context.user_data.clear()' in lines[i+1]:
            new_lines.append('')
            new_lines.append('    # Auto-send receipt to staff Telegram chat')
            new_lines.append('    receipt_data = {')
            new_lines.append('        "type": "topup", "voucher_id": tu_vid, "date": today,')
            new_lines.append('        "member_id": tu_id, "rank": r_saved, "amount": tu_amt,')
            new_lines.append('        "base_mins": tu_base, "bonus_mins": tu_bonus, "total_mins": tu_mins,')
            new_lines.append('        "kpay": tu_kpay, "cash": tu_cash, "phone": tu_phone,')
            new_lines.append('        "balance_mins": bal_mins, "prev_balance": prev_bal,')
            new_lines.append('        "balance_change": tu_mins, "balance_after": bal_mins,')
            new_lines.append('    }')
            new_lines.append('    asyncio.create_task(auto_generate_receipt(update, context, tu_vid, receipt_data))')
            new_lines.append('')
            found = True
            print("+ Added auto_generate_receipt call (flexible match)")
            changes += 1
        i += 1
    if found:
        content = '\n'.join(new_lines)
    else:
        print("ERROR: Could not find get_receipt_kb + context.user_data.clear() pattern")
        # Debug
        for i, line in enumerate(content.split('\n')):
            if 'get_receipt_kb' in line:
                print(f"  get_receipt_kb at line {i+1}: {line.strip()}")
                if i+1 < len(content.split('\n')):
                    print(f"  Next line: {content.split(chr(10))[i+1].strip()}")
        sys.exit(1)

# Write back
with open('/root/psvibe-sales-bot/bot/handlers/members.py', 'w') as f:
    f.write(content)

print(f"\nDone: {changes} changes applied to members.py")
