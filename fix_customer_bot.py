#!/usr/bin/env python3
"""Apply remaining Phase 2 fixes: cache sweeper + registration in main()."""
filepath = "/root/Sales-Tele-Bot_staging/customer_bot.py"
with open(filepath, "r") as f:
    content = f.read()

print(f"Current length: {len(content)}")

# TASK 6: Insert _async_cache_sweeper after _cache_pop and before _split_message
old = """def _cache_pop(key: str):
    # Thread/async-safe pop with lock
    with _CACHE_LOCK:
        return _CACHE.pop(key, None)


def _split_message(text: str, limit: int = 4000) -> list[str]:"""

new = '''def _cache_pop(key: str):
    # Thread/async-safe pop with lock
    with _CACHE_LOCK:
        return _CACHE.pop(key, None)


async def _async_cache_sweeper():
    """Background task: prune expired cache entries every 300 seconds (5 min).
    Prevents unbounded memory growth from stale cached data."""
    await asyncio.sleep(30)  # initial delay to let bot stabilise
    while not _shutdown_event.is_set():
        try:
            now = time.time()
            with _CACHE_LOCK:
                expired = [
                    key for key, entry in _CACHE.items()
                    if (now - entry["ts"]) >= entry.get("ttl", _CACHE_TTL)
                ]
                for key in expired:
                    del _CACHE[key]
            if expired:
                logging.debug("Cache sweeper: pruned %d expired entries: %s", len(expired), expired)
        except Exception as e:
            logging.warning("Cache sweeper error: %s", e)
        try:
            await asyncio.wait_for(_shutdown_event.wait(), timeout=300)
            logging.info("Cache sweeper: shutdown signal received, stopping")
            break
        except asyncio.TimeoutError:
            continue


def _split_message(text: str, limit: int = 4000) -> list[str]:'''

assert old in content, "cache_pop -> _split_message section not found!"
content = content.replace(old, new, 1)
print("✓ cache sweeper function added")

# Register sweeper in main() after shutdown event setup
old2 = '    _shutdown_task = asyncio.create_task(_shutdown_event.wait())\n    _shutdown_event.add_done_callback(lambda _: logging.info("Shutdown signal processed"))'
assert old2 in content, "shutdown registration not found!"
content = content.replace(old2, old2 + '\n    asyncio.create_task(_async_cache_sweeper())', 1)
print("✓ cache sweeper registered in main()")

with open(filepath, "w") as f:
    f.write(content)

print(f"Final length: {len(content)}")
print("OK: All customer_bot.py Phase 2 modifications complete")
