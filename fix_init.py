#!/usr/bin/env python3
"""Fix the damaged section of bot/__init__.py"""
import sys

path = "/root/psvibe-sales-bot/bot/__init__.py"

with open(path) as f:
    content = f.read()

# The _pin_then and fetch_payment_methods functions lost their quotes.
# Find and replace the damaged block.

old_marker = "# ── PIN-then-action wrapper ──"
import_marker = "from bot.handlers import *  # noqa: F401,F403,E402"

old_start = content.find(old_marker)
import_start = content.find(import_marker)

if old_start < 0 or import_start < 0:
    print(f"ERROR: Could not find markers (start={old_start}, import={import_start})")
    sys.exit(1)

new_block = """# ── PIN-then-action wrapper ──
async def _pin_then(after: str, label: str, update, context):
    \"\"\"Store target action, prompt for PIN, return ADMIN_PIN state.\"\"\"
    context.user_data["_after_pin"] = after
    await update.message.reply_text(
        f"\\U0001f510 *{label}* PIN \\u101b\\u102d\\u102f\\u1000\\u103a\\u1011\\u100a\\u1037\\u103a\\u1015\\u102b -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ADMIN_PIN


# ── Payment Methods Fetcher ──
def fetch_payment_methods():
    \"\"\"Return list of payment method options, with API-backed fallback.\"\"\"
    try:
        data = _replit_get("sheets/payment-methods")
        if isinstance(data, dict) and "methods" in data:
            return data["methods"]
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return list(PAY_METHODS)


"""

content = content[:old_start] + new_block + content[import_start:]

with open(path, "w") as f:
    f.write(content)

print("Applied fix for _pin_then and fetch_payment_methods")
