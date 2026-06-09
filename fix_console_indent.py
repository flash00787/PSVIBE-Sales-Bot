#!/usr/bin/env python3
"""Fix indentation error in console.py - restore full function footer."""

with open("/root/psvibe-sales-bot/bot/handlers/console.py", "r") as f:
    c = f.read()

# Find the problematic area
i = c.rfind("CashBack Coupon: Auto-generated via MySQL API")
if i < 0:
    i = c.rfind("CashBack Coupon")

# Find the end of the coupon block
e = c.find("booking_id=_linked_bk_id)", i)
if e < 0:
    print("FAIL: cannot find booking_id line")
    exit(1)

# Find where the except ends - look for the pattern
exc_end = c.rfind("logger.warning", i, e)
if exc_end < 0:
    print("FAIL: cannot find logger.warning")
    exit(1)
exc_end = c.find("\n", exc_end) + 1

# The correct replacement from the except to the end
old_block = c[exc_end:e + len("booking_id=_linked_bk_id)")]

new_footer = """\
    except Exception as cb_e:
        logger.warning("Cashback coupon generation failed (non-critical): %s", cb_e)

    from bot.handlers.sales import launch_session_sale
    return await launch_session_sale(update, context, cid, mbr, total_mins, session_staff,
                                     booking_id=_linked_bk_id)"""

c = c.replace(old_block, new_footer)

# Verify Python syntax
try:
    compile(c, "console.py", "exec")
    print("SUCCESS: syntax OK!")
except SyntaxError as se:
    print(f"SYNTAX ERROR: {se}")
    # Find the line with error
    lines = c.split("\n")
    error_line = se.lineno
    if error_line:
        for l in range(max(0,error_line-5), min(len(lines), error_line+3)):
            prefix = ">>>" if l+1 == error_line else "   "
            print(f"{prefix} {l+1}: {lines[l]}")
    exit(1)

with open("/root/psvibe-sales-bot/bot/handlers/console.py", "w") as f:
    f.write(c)
print("SUCCESS: Indent fixed!")
