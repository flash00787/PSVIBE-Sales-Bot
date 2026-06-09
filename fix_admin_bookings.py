#!/usr/bin/env python3
"""Fix IndentationError in admin_bookings.py"""
path = "/root/psvibe-sales-bot/bot/handlers/admin_bookings.py"
with open(path) as f:
    content = f.read()

# Fix 1: except body not indented
old1 = '    except Exception as e:\n    logger.error("cb_booking_mgmt error: %s", e, exc_info=True)\n        return'
new1 = '    except Exception as e:\n        logger.error("cb_booking_mgmt error: %s", e, exc_info=True)\n        return'
content = content.replace(old1, new1)

# Fix 2: except inside edit_fn not properly indented
old2 = '        try:\n            await query.edit_message_text(text, **kw)\n    except Exception as e:\n            logger.error("HANDLER_ERROR: edit_booking_card_inline", exc_info=True)'
new2 = '        try:\n            await query.edit_message_text(text, **kw)\n        except Exception as e:\n            logger.error("HANDLER_ERROR: edit_booking_card_inline", exc_info=True)'
content = content.replace(old2, new2)

with open(path, "w") as f:
    f.write(content)
print("Fixed admin_bookings.py")
