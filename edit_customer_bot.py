#!/usr/bin/env python3
"""Apply Phase 2 fixes to customer_bot.py: API retry logic, bare except logging, cache sweeper."""
import re

filepath = "/root/Sales-Tele-Bot_staging/customer_bot.py"
with open(filepath, "r") as f:
    content = f.read()

print(f"Original length: {len(content)}")

# ══════════════════════════════════════════════════════════════════════════════
# TASK 4: API Retry Logic with Exponential Backoff
# Add retry loop (up to 3 retries, 1s→2s→4s) for:
#    urllib.error.URLError, TimeoutError, ConnectionError,
#    http.client.HTTPException, OSError
# Non-retryable: HTTPError (4xx/5xx), other Exception
# ══════════════════════════════════════════════════════════════════════════════

# --- _api_get ---
old = '''def _api_get(path: str):
    if not API_BASE:
        logging.warning("api_get: API_BASE not set")
        return None
    try:
        _rg = _req.Request(f"{API_BASE}/api/{path}", headers={"X-API-Key": _API_KEY})
        with _req.urlopen(_rg, timeout=15) as r:
            return json.load(r)
    except Exception as e:
        logging.warning("api_get %s: %s", path, e)
        return None'''
new = '''def _api_get(path: str):
    if not API_BASE:
        logging.warning("api_get: API_BASE not set")
        return None
    import urllib.error as _urlerr
    import http.client as _http
    for attempt in range(4):  # 1 initial + 3 retries
        try:
            _rg = _req.Request(f"{API_BASE}/api/{path}", headers={"X-API-Key": _API_KEY})
            with _req.urlopen(_rg, timeout=15) as r:
                return json.load(r)
        except _urlerr.HTTPError as e:
            logging.warning("api_get %s HTTP %s — non-retryable", path, e.code)
            return None
        except (_urlerr.URLError, TimeoutError, ConnectionError,
                _http.HTTPException, OSError) as e:
            if attempt < 3:
                delay = 2 ** attempt  # 1s, 2s, 4s
                logging.warning("api_get %s attempt %d/4 failed (retry in %ds): %s", path, attempt + 1, delay, e)
                time.sleep(delay)
            else:
                logging.error("api_get %s FAILED after 4 attempts: %s", path, e)
                return None
        except Exception as e:
            logging.warning("api_get %s: %s", path, e)
            return None
    return None'''
assert old in content, "old _api_get not found!"
content = content.replace(old, new, 1)
print("✓ _api_get replaced")

# --- _api_post ---
old = '''def _api_post(path: str, body: dict):
    """POST JSON to API. Returns parsed response dict, or error dict on 4xx, or None on network error."""
    if not API_BASE:
        return None
    import urllib.error as _urlerr
    try:
        data = json.dumps(body).encode()
        r = _req.Request(f"{API_BASE}/api/{path}", data=data,
                         headers={"Content-Type": "application/json", "X-API-Key": _API_KEY}, method="POST")
        with _req.urlopen(r, timeout=15) as resp:
            return json.load(resp)
    except _urlerr.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode())
        except Exception:
            err_body = {"error": f"http_{e.code}"}
        err_body["__status__"] = e.code
        logging.warning("api_post %s HTTP %s: %s", path, e.code, err_body)
        return err_body
    except Exception as e:
        logging.warning("api_post %s: %s", path, e)
        return None'''
new = '''def _api_post(path: str, body: dict):
    """POST JSON to API. Returns parsed response dict, or error dict on 4xx, or None on network error."""
    if not API_BASE:
        return None
    import urllib.error as _urlerr
    import http.client as _http
    for attempt in range(4):  # 1 initial + 3 retries
        try:
            data = json.dumps(body).encode()
            r = _req.Request(f"{API_BASE}/api/{path}", data=data,
                             headers={"Content-Type": "application/json", "X-API-Key": _API_KEY}, method="POST")
            with _req.urlopen(r, timeout=15) as resp:
                return json.load(resp)
        except _urlerr.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode())
            except Exception:
                err_body = {"error": f"http_{e.code}"}
            err_body["__status__"] = e.code
            logging.warning("api_post %s HTTP %s: %s", path, e.code, err_body)
            return err_body
        except (_urlerr.URLError, TimeoutError, ConnectionError,
                _http.HTTPException, OSError) as e:
            if attempt < 3:
                delay = 2 ** attempt
                logging.warning("api_post %s attempt %d/4 failed (retry in %ds): %s", path, attempt + 1, delay, e)
                time.sleep(delay)
            else:
                logging.error("api_post %s FAILED after 4 attempts: %s", path, e)
                return None
        except Exception as e:
            logging.warning("api_post %s: %s", path, e)
            return None
    return None'''
assert old in content, "old _api_post not found!"
content = content.replace(old, new, 1)
print("✓ _api_post replaced")

# --- _api_patch ---
old = '''def _api_patch(path: str, body: dict):
    """PATCH JSON to API. Returns parsed response dict, or error dict on 4xx, or None on network error."""
    if not API_BASE:
        return None
    import urllib.error as _urlerr
    try:
        data = json.dumps(body).encode()
        r = _req.Request(f"{API_BASE}/api/{path}", data=data,
                         headers={"Content-Type": "application/json", "X-API-Key": _API_KEY}, method="PATCH")
        with _req.urlopen(r, timeout=15) as resp:
            return json.loads(resp.read())
    except _urlerr.HTTPError as e:
        # Parse 4xx error body (e.g. 409 console_conflict) instead of silently returning None
        try:
            err_body = json.loads(e.read().decode())
        except Exception:
            err_body = {"error": f"http_{e.code}"}
        err_body["__status__"] = e.code
        logging.warning("api_patch %s HTTP %s: %s", path, e.code, err_body)
        return err_body
    except Exception as e:
        logging.error("api_patch %s: %s", path, e)
        return None'''
new = '''def _api_patch(path: str, body: dict):
    """PATCH JSON to API. Returns parsed response dict, or error dict on 4xx, or None on network error."""
    if not API_BASE:
        return None
    import urllib.error as _urlerr
    import http.client as _http
    for attempt in range(4):  # 1 initial + 3 retries
        try:
            data = json.dumps(body).encode()
            r = _req.Request(f"{API_BASE}/api/{path}", data=data,
                             headers={"Content-Type": "application/json", "X-API-Key": _API_KEY}, method="PATCH")
            with _req.urlopen(r, timeout=15) as resp:
                return json.loads(resp.read())
        except _urlerr.HTTPError as e:
            # Parse 4xx error body (e.g. 409 console_conflict) instead of silently returning None
            try:
                err_body = json.loads(e.read().decode())
            except Exception:
                err_body = {"error": f"http_{e.code}"}
            err_body["__status__"] = e.code
            logging.warning("api_patch %s HTTP %s: %s", path, e.code, err_body)
            return err_body
        except (_urlerr.URLError, TimeoutError, ConnectionError,
                _http.HTTPException, OSError) as e:
            if attempt < 3:
                delay = 2 ** attempt
                logging.warning("api_patch %s attempt %d/4 failed (retry in %ds): %s", path, attempt + 1, delay, e)
                time.sleep(delay)
            else:
                logging.error("api_patch %s FAILED after 4 attempts: %s", path, e)
                return None
        except Exception as e:
            logging.error("api_patch %s: %s", path, e)
            return None
    return None'''
assert old in content, "old _api_patch not found!"
content = content.replace(old, new, 1)
print("✓ _api_patch replaced")

# --- _api_delete ---
old = '''def _api_delete(path: str):
    """DELETE request to API. Returns parsed response or None."""
    if not API_BASE:
        return None
    import urllib.error as _urlerr
    try:
        r = _req.Request(f"{API_BASE}/api/{path}", headers={"X-API-Key": _API_KEY}, method="DELETE")
        with _req.urlopen(r, timeout=10) as resp:
            return json.load(resp)
    except _urlerr.HTTPError as e:
        logging.warning("api_delete %s HTTP %s", path, e.code)
        return None
    except Exception as e:
        logging.warning("api_delete %s: %s", path, e)
        return None'''
new = '''def _api_delete(path: str):
    """DELETE request to API. Returns parsed response or None."""
    if not API_BASE:
        return None
    import urllib.error as _urlerr
    import http.client as _http
    for attempt in range(4):  # 1 initial + 3 retries
        try:
            r = _req.Request(f"{API_BASE}/api/{path}", headers={"X-API-Key": _API_KEY}, method="DELETE")
            with _req.urlopen(r, timeout=10) as resp:
                return json.load(resp)
        except _urlerr.HTTPError as e:
            logging.warning("api_delete %s HTTP %s", path, e.code)
            return None
        except (_urlerr.URLError, TimeoutError, ConnectionError,
                _http.HTTPException, OSError) as e:
            if attempt < 3:
                delay = 2 ** attempt
                logging.warning("api_delete %s attempt %d/4 failed (retry in %ds): %s", path, attempt + 1, delay, e)
                time.sleep(delay)
            else:
                logging.error("api_delete %s FAILED after 4 attempts: %s", path, e)
                return None
        except Exception as e:
            logging.warning("api_delete %s: %s", path, e)
            return None
    return None'''
assert old in content, "old _api_delete not found!"
content = content.replace(old, new, 1)
print("✓ _api_delete replaced")

# --- _tg_send ---
old = '''def _tg_send(body: dict):
    import urllib.error
    data = json.dumps(body).encode()
    r = _req.Request(
        f"https://api.telegram.org/bot{CUSTOMER_BOT_TOKEN}/sendMessage",
        data=data, headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with _req.urlopen(r, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        logging.error("tg_send HTTP %s — %s", e.code, detail)
        return None
    except Exception as e:
        logging.warning("tg_send failed: %s", e)
        return None'''
new = '''def _tg_send(body: dict):
    import urllib.error as _urlerr
    import http.client as _http
    data = json.dumps(body).encode()
    r = _req.Request(
        f"https://api.telegram.org/bot{CUSTOMER_BOT_TOKEN}/sendMessage",
        data=data, headers={"Content-Type": "application/json"}, method="POST",
    )
    for attempt in range(4):  # 1 initial + 3 retries
        try:
            with _req.urlopen(r, timeout=15) as resp:
                return json.loads(resp.read())
        except _urlerr.HTTPError as e:
            detail = e.read().decode(errors="replace")
            logging.error("tg_send HTTP %s — %s", e.code, detail)
            return None
        except (_urlerr.URLError, TimeoutError, ConnectionError,
                _http.HTTPException, OSError) as e:
            if attempt < 3:
                delay = 2 ** attempt
                logging.warning("tg_send attempt %d/4 failed (retry in %ds): %s", attempt + 1, delay, e)
                time.sleep(delay)
            else:
                logging.error("tg_send FAILED after 4 attempts: %s", e)
                return None
        except Exception as e:
            logging.warning("tg_send failed: %s", e)
            return None
    return None'''
assert old in content, "old _tg_send not found!"
content = content.replace(old, new, 1)
print("✓ _tg_send replaced")

# ══════════════════════════════════════════════════════════════════════════════
# TASK 5: Bare Exception Logging — Critical Areas
# ══════════════════════════════════════════════════════════════════════════════

# 1. waitlist auto-claim in cmd_book
old = '''    except Exception:
        pass
    context.user_data.clear()
    kb = ReplyKeyboardMarkup(
        [[BTN_HAS_CARD_YES, BTN_HAS_CARD_NO], [BTN_CANCEL]],
        resize_keyboard=True, one_time_keyboard=True,
    )
    await update.message.reply_text(
        _step_hdr(1, 9, "Member Card") +'''
assert old in content, "wl_claim pass not found!"
content = content.replace(old, '''    except Exception as e:
        logging.error("cmd_book: waitlist auto-claim failed: %s", e)
    context.user_data.clear()
    kb = ReplyKeyboardMarkup(
        [[BTN_HAS_CARD_YES, BTN_HAS_CARD_NO], [BTN_CANCEL]],
        resize_keyboard=True, one_time_keyboard=True,
    )
    await update.message.reply_text(
        _step_hdr(1, 9, "Member Card") +''', 1)
print("✓ waitlist auto-claim logged")

# 2. waitlist reserved_until parse
old = '''                        except Exception:
                            pass
                    await update.message.reply_text('''
assert old in content, "wl reserved parse not found!"
content = content.replace(old, '''                        except Exception as e:
                            logging.warning("waitlist reserved_until parse failed: %s", e)
                    await update.message.reply_text(''', 1)
print("✓ waitlist reserved_until parse logged")

# 3. persist_sent_sets I/O
old = '''    except Exception:
        pass

_reminders_sent, _checkins_sent = _load_sent_sets()'''
assert old in content, "persist_sent_sets pass not found!"
content = content.replace(old, '''    except Exception as e:
        logging.warning("Failed to persist sent reminder/checkin IDs: %s", e)

_reminders_sent, _checkins_sent = _load_sent_sets()''', 1)
print("✓ persist_sent_sets logged")

# 4. load_sent_sets I/O
old = '''    try:
        with open(_SENT_FILE) as f:
            d = json.load(f)
        return set(d.get("reminders", [])), set(d.get("checkins", []))
    except Exception:
        return set(), set()'''
assert old in content, "load_sent_sets not found!"
content = content.replace(old, '''    try:
        with open(_SENT_FILE) as f:
            d = json.load(f)
        return set(d.get("reminders", [])), set(d.get("checkins", []))
    except Exception as e:
        logging.warning("Failed to load sent reminder/checkin IDs from %s: %s", _SENT_FILE, e)
        return set(), set()''', 1)
print("✓ load_sent_sets logged")

# 5. startup booking re-queue time parse
old = '''            except Exception:
                pass
        if requeued:'''
assert old in content, "startup requeue pass not found!"
content = content.replace(old, '''            except Exception as e:
                logging.warning("startup booking re-queue time parse failed for bk #%s: %s", bk.get("id"), e)
        if requeued:''', 1)
print("✓ startup requeue time parse logged")

# 6. booking duplicate check API (near booking submit)
old = '''    except Exception:
        existing = []

    bk_date = d.get("bk_date", "")'''
assert old in content, "dup booking check not found!"
content = content.replace(old, '''    except Exception as e:
        logging.error("Booking duplicate check API failed for uid=%s: %s", uid, e)
        existing = []

    bk_date = d.get("bk_date", "")''', 1)
print("✓ duplicate booking check logged")

# ══════════════════════════════════════════════════════════════════════════════
# TASK 6: Cache Pruning Sweeper
# ══════════════════════════════════════════════════════════════════════════════

# Insert _async_cache_sweeper after _cache_pop and before WL_PREF
old = '''def _cache_pop(key: str):
    # Thread/async-safe pop with lock
    with _CACHE_LOCK:
        return _CACHE.pop(key, None)


# ── Waitlist conversation states (100-103, no clash with BK_ 0-14) ────────────
WL_PREF, WL_NAME, WL_PHONE, WL_CONFIRM = range(100, 104)'''
new = '''def _cache_pop(key: str):
    # Thread/async-safe pop with lock
    with _CACHE_LOCK:
        return _CACHE.pop(key, None)


# ── Waitlist conversation states (100-103, no clash with BK_ 0-14) ────────────
WL_PREF, WL_NAME, WL_PHONE, WL_CONFIRM = range(100, 104)


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
            continue'''
assert old in content, "cache end section not found!"
content = content.replace(old, new, 1)
print("✓ cache sweeper function added")

# Register sweeper in main() after shutdown event setup
old = '    _shutdown_task = asyncio.create_task(_shutdown_event.wait())\n    _shutdown_event.add_done_callback(lambda _: logging.info("Shutdown signal processed"))'
assert old in content, "shutdown registration not found!"
content = content.replace(old, old + '\n    asyncio.create_task(_async_cache_sweeper())', 1)
print("✓ cache sweeper registered in main()")

# Write the modified file
with open(filepath, "w") as f:
    f.write(content)

print(f"Final length: {len(content)}")
print("✓ customer_bot.py Phase 2 modifications complete")
