#!/usr/bin/env python3
"""Add customer notification when cashback coupon is generated.
Insert call to send_cashback_coupon_notification after coupon is shown in receipt."""

with open("/root/psvibe-sales-bot/bot/handlers/sales.py", "r") as f:
    c = f.read()

# Find the coupon_line section where we send coupon notification
# We need to call send_cashback_coupon_notification when coupon_code exists
# Find the customer chat id line
notify_call = (
    '        if coupon_code:\n'
    '            await update.message.reply_text(\n'
    '                f"🎫 *100% CashBack Coupon!*\\n"\n'
    '                f"Code: `{coupon_code}`\\n"\n'
    '                f"Minutes: *{coupon_mins} mins*\\n"\n'
    '                f"\\u23f0 နောက်လာရင် ဒီ code ကို ပြပြီး ပြန်ဆော့လို့ရပါတယ်!",\n'
    '                parse_mode="Markdown",\n'
    '            )\n\n'
)

# After that block, add customer notification
after_notify = (
    '        if coupon_code:\n'
    '            await update.message.reply_text(\n'
    '                f"🎫 *100% CashBack Coupon!*\\n"\n'
    '                f"Code: `{coupon_code}`\\n"\n'
    '                f"Minutes: *{coupon_mins} mins*\\n"\n'
    '                f"\\u23f0 နောက်လာရင် ဒီ code ကို ပြပြီး ပြန်ဆော့လို့ရပါတယ်!",\n'
    '                parse_mode="Markdown",\n'
    '            )\n'
    '            # Also notify customer via Telegram\n'
    '            try:\n'
    '                from bot.handlers.notify import send_cashback_coupon_notification\n'
    '                chat_id = await asyncio.to_thread(get_customer_chat_id, _m_id)\n'
    '                if chat_id:\n'
    '                    await send_cashback_coupon_notification(context, chat_id, coupon_code, _m_id, coupon_mins)\n'
    '            except Exception as _ce:\n'
    '                logging.warning("send_cashback_coupon_notification failed: %s", _ce)\n\n'
)

# Replace the existing coupon notification block
c = c.replace(notify_call, after_notify)

with open("/root/psvibe-sales-bot/bot/handlers/sales.py", "w") as f:
    f.write(c)
print("SUCCESS: Customer notification added for coupons!")
