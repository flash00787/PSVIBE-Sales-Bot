#!/usr/bin/env python3
filepath = "/root/Sales-Tele-Bot_staging/customer_bot.py"
with open(filepath, "r") as f:
    content = f.read()

# Register sweeper in _post_init alongside other background tasks
old = '        asyncio.create_task(_cache_invalidation_listener())\n        logging.info("Booking scheduler started | Cache listener started | Commands registered")'
new = '        asyncio.create_task(_cache_invalidation_listener())\n        asyncio.create_task(_async_cache_sweeper())\n        logging.info("Booking scheduler started | Cache listener started | Cache sweeper started | Commands registered")'
assert old in content, "post_init tasks not found!"
content = content.replace(old, new, 1)
print("OK: cache sweeper registered in _post_init()")

with open(filepath, "w") as f:
    f.write(content)
print("DONE")
