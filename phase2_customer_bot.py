#!/usr/bin/env python3
"""Apply ALL Phase 2 fixes to customer_bot.py in one pass."""
filepath = "/root/Sales-Tele-Bot_staging/customer_bot.py"
with open(filepath, "r") as f:
    content = f.read()

print(f"Original length: {len(content)}, lines: {content.count(chr(10))}")

# ══════════════════════════════════════════════════════════════════════════════
# TASK 4: API Retry Logic (5 functions)
# ══════════════════════════════════════════════════════════════════════════════

# 1. _api_get
old = "def _api_get(path: str):\n    if not API_BASE:\n        logging.warning(\"api_get: API_BASE not set\")\n        return None\n    try:\n        _rg = _req.Request(f\"{API_BASE}/api/{path}\", headers={\"X-API-Key\": _API_KEY})\n        with _req.urlopen(_rg, timeout=15) as r:\n            return json.load(r)\n    except Exception as e:\n        logging.warning(\"api_get %s: %s\", path, e)\n        return None"
new = "def _api_get(path: str):\n    if not API_BASE:\n        logging.warning(\"api_get: API_BASE not set\")\n        return None\n    import urllib.error as _urlerr\n    import http.client as _http\n    for attempt in range(4):  # 1 initial + 3 retries\n        try:\n            _rg = _req.Request(f\"{API_BASE}/api/{path}\", headers={\"X-API-Key\": _API_KEY})\n            with _req.urlopen(_rg, timeout=15) as r:\n                return json.load(r)\n        except _urlerr.HTTPError as e:\n            logging.warning(\"api_get %s HTTP %s \\u2014 non-retryable\", path, e.code)\n            return None\n        except (_urlerr.URLError, TimeoutError, ConnectionError,\n                _http.HTTPException, OSError) as e:\n            if attempt < 3:\n                delay = 2 ** attempt  # 1s, 2s, 4s\n                logging.warning(\"api_get %s attempt %d/4 failed (retry in %ds): %s\", path, attempt + 1, delay, e)\n                time.sleep(delay)\n            else:\n                logging.error(\"api_get %s FAILED after 4 attempts: %s\", path, e)\n                return None\n        except Exception as e:\n            logging.warning(\"api_get %s: %s\", path, e)\n            return None\n    return None"
if old in content:
    content = content.replace(old, new, 1)
    print("OK _api_get")
else:
    print("MISS _api_get")

# 2. _api_post
old = "def _api_post(path: str, body: dict):\n    \"\"\"POST JSON to API. Returns parsed response dict, or error dict on 4xx, or None on network error.\"\"\"\n    if not API_BASE:\n        return None\n    import urllib.error as _urlerr\n    try:\n        data = json.dumps(body).encode()\n        r = _req.Request(f\"{API_BASE}/api/{path}\", data=data,\n                         headers={\"Content-Type\": \"application/json\", \"X-API-Key\": _API_KEY}, method=\"POST\")\n        with _req.urlopen(r, timeout=15) as resp:\n            return json.load(resp)\n    except _urlerr.HTTPError as e:\n        try:\n            err_body = json.loads(e.read().decode())\n        except Exception:\n            err_body = {\"error\": f\"http_{e.code}\"}\n        err_body[\"__status__\"] = e.code\n        logging.warning(\"api_post %s HTTP %s: %s\", path, e.code, err_body)\n        return err_body\n    except Exception as e:\n        logging.warning(\"api_post %s: %s\", path, e)\n        return None"
new = "def _api_post(path: str, body: dict):\n    \"\"\"POST JSON to API. Returns parsed response dict, or error dict on 4xx, or None on network error.\"\"\"\n    if not API_BASE:\n        return None\n    import urllib.error as _urlerr\n    import http.client as _http\n    for attempt in range(4):  # 1 initial + 3 retries\n        try:\n            data = json.dumps(body).encode()\n            r = _req.Request(f\"{API_BASE}/api/{path}\", data=data,\n                             headers={\"Content-Type\": \"application/json\", \"X-API-Key\": _API_KEY}, method=\"POST\")\n            with _req.urlopen(r, timeout=15) as resp:\n                return json.load(resp)\n        except _urlerr.HTTPError as e:\n            try:\n                err_body = json.loads(e.read().decode())\n            except Exception:\n                err_body = {\"error\": f\"http_{e.code}\"}\n            err_body[\"__status__\"] = e.code\n            logging.warning(\"api_post %s HTTP %s: %s\", path, e.code, err_body)\n            return err_body\n        except (_urlerr.URLError, TimeoutError, ConnectionError,\n                _http.HTTPException, OSError) as e:\n            if attempt < 3:\n                delay = 2 ** attempt\n                logging.warning(\"api_post %s attempt %d/4 failed (retry in %ds): %s\", path, attempt + 1, delay, e)\n                time.sleep(delay)\n            else:\n                logging.error(\"api_post %s FAILED after 4 attempts: %s\", path, e)\n                return None\n        except Exception as e:\n            logging.warning(\"api_post %s: %s\", path, e)\n            return None\n    return None"
if old in content:
    content = content.replace(old, new, 1)
    print("OK _api_post")
else:
    print("MISS _api_post")

# 3. _api_patch
old = "def _api_patch(path: str, body: dict):\n    \"\"\"PATCH JSON to API. Returns parsed response dict, or error dict on 4xx, or None on network error.\"\"\"\n    if not API_BASE:\n        return None\n    import urllib.error as _urlerr\n    try:\n        data = json.dumps(body).encode()\n        r = _req.Request(f\"{API_BASE}/api/{path}\", data=data,\n                         headers={\"Content-Type\": \"application/json\", \"X-API-Key\": _API_KEY}, method=\"PATCH\")\n        with _req.urlopen(r, timeout=15) as resp:\n            return json.loads(resp.read())\n    except _urlerr.HTTPError as e:\n        # Parse 4xx error body (e.g. 409 console_conflict) instead of silently returning None\n        try:\n            err_body = json.loads(e.read().decode())\n        except Exception:\n            err_body = {\"error\": f\"http_{e.code}\"}\n        err_body[\"__status__\"] = e.code\n        logging.warning(\"api_patch %s HTTP %s: %s\", path, e.code, err_body)\n        return err_body\n    except Exception as e:\n        logging.error(\"api_patch %s: %s\", path, e)\n        return None"
new = "def _api_patch(path: str, body: dict):\n    \"\"\"PATCH JSON to API. Returns parsed response dict, or error dict on 4xx, or None on network error.\"\"\"\n    if not API_BASE:\n        return None\n    import urllib.error as _urlerr\n    import http.client as _http\n    for attempt in range(4):  # 1 initial + 3 retries\n        try:\n            data = json.dumps(body).encode()\n            r = _req.Request(f\"{API_BASE}/api/{path}\", data=data,\n                             headers={\"Content-Type\": \"application/json\", \"X-API-Key\": _API_KEY}, method=\"PATCH\")\n            with _req.urlopen(r, timeout=15) as resp:\n                return json.loads(resp.read())\n        except _urlerr.HTTPError as e:\n            # Parse 4xx error body (e.g. 409 console_conflict) instead of silently returning None\n            try:\n                err_body = json.loads(e.read().decode())\n            except Exception:\n                err_body = {\"error\": f\"http_{e.code}\"}\n            err_body[\"__status__\"] = e.code\n            logging.warning(\"api_patch %s HTTP %s: %s\", path, e.code, err_body)\n            return err_body\n        except (_urlerr.URLError, TimeoutError, ConnectionError,\n                _http.HTTPException, OSError) as e:\n            if attempt < 3:\n                delay = 2 ** attempt\n                logging.warning(\"api_patch %s attempt %d/4 failed (retry in %ds): %s\", path, attempt + 1, delay, e)\n                time.sleep(delay)\n            else:\n                logging.error(\"api_patch %s FAILED after 4 attempts: %s\", path, e)\n                return None\n        except Exception as e:\n            logging.error(\"api_patch %s: %s\", path, e)\n            return None\n    return None"
if old in content:
    content = content.replace(old, new, 1)
    print("OK _api_patch")
else:
    print("MISS _api_patch")

# 4. _api_delete
old = "def _api_delete(path: str):\n    \"\"\"DELETE request to API. Returns parsed response or None.\"\"\"\n    if not API_BASE:\n        return None\n    import urllib.error as _urlerr\n    try:\n        r = _req.Request(f\"{API_BASE}/api/{path}\", headers={\"X-API-Key\": _API_KEY}, method=\"DELETE\")\n        with _req.urlopen(r, timeout=10) as resp:\n            return json.load(resp)\n    except _urlerr.HTTPError as e:\n        logging.warning(\"api_delete %s HTTP %s\", path, e.code)\n        return None\n    except Exception as e:\n        logging.warning(\"api_delete %s: %s\", path, e)\n        return None"
new = "def _api_delete(path: str):\n    \"\"\"DELETE request to API. Returns parsed response or None.\"\"\"\n    if not API_BASE:\n        return None\n    import urllib.error as _urlerr\n    import http.client as _http\n    for attempt in range(4):  # 1 initial + 3 retries\n        try:\n            r = _req.Request(f\"{API_BASE}/api/{path}\", headers={\"X-API-Key\": _API_KEY}, method=\"DELETE\")\n            with _req.urlopen(r, timeout=10) as resp:\n                return json.load(resp)\n        except _urlerr.HTTPError as e:\n            logging.warning(\"api_delete %s HTTP %s\", path, e.code)\n            return None\n        except (_urlerr.URLError, TimeoutError, ConnectionError,\n                _http.HTTPException, OSError) as e:\n            if attempt < 3:\n                delay = 2 ** attempt\n                logging.warning(\"api_delete %s attempt %d/4 failed (retry in %ds): %s\", path, attempt + 1, delay, e)\n                time.sleep(delay)\n            else:\n                logging.error(\"api_delete %s FAILED after 4 attempts: %s\", path, e)\n                return None\n        except Exception as e:\n            logging.warning(\"api_delete %s: %s\", path, e)\n            return None\n    return None"
if old in content:
    content = content.replace(old, new, 1)
    print("OK _api_delete")
else:
    print("MISS _api_delete")

# 5. _tg_send
old = "def _tg_send(body: dict):\n    import urllib.error\n    data = json.dumps(body).encode()\n    r = _req.Request(\n        f\"https://api.telegram.org/bot{CUSTOMER_BOT_TOKEN}/sendMessage\",\n        data=data, headers={\"Content-Type\": \"application/json\"}, method=\"POST\",\n    )\n    try:\n        with _req.urlopen(r, timeout=15) as resp:\n            return json.loads(resp.read())\n    except urllib.error.HTTPError as e:\n        detail = e.read().decode(errors=\"replace\")\n        logging.error(\"tg_send HTTP %s \\u2014 %s\", e.code, detail)\n        return None\n    except Exception as e:\n        logging.warning(\"tg_send failed: %s\", e)\n        return None"
new = "def _tg_send(body: dict):\n    import urllib.error as _urlerr\n    import http.client as _http\n    data = json.dumps(body).encode()\n    r = _req.Request(\n        f\"https://api.telegram.org/bot{CUSTOMER_BOT_TOKEN}/sendMessage\",\n        data=data, headers={\"Content-Type\": \"application/json\"}, method=\"POST\",\n    )\n    for attempt in range(4):  # 1 initial + 3 retries\n        try:\n            with _req.urlopen(r, timeout=15) as resp:\n                return json.loads(resp.read())\n        except _urlerr.HTTPError as e:\n            detail = e.read().decode(errors=\"replace\")\n            logging.error(\"tg_send HTTP %s \\u2014 %s\", e.code, detail)\n            return None\n        except (_urlerr.URLError, TimeoutError, ConnectionError,\n                _http.HTTPException, OSError) as e:\n            if attempt < 3:\n                delay = 2 ** attempt\n                logging.warning(\"tg_send attempt %d/4 failed (retry in %ds): %s\", attempt + 1, delay, e)\n                time.sleep(delay)\n            else:\n                logging.error(\"tg_send FAILED after 4 attempts: %s\", e)\n                return None\n        except Exception as e:\n            logging.warning(\"tg_send failed: %s\", e)\n            return None\n    return None"
if old in content:
    content = content.replace(old, new, 1)
    print("OK _tg_send")
else:
    print("MISS _tg_send")

# ══════════════════════════════════════════════════════════════════════════════
# TASK 5: Bare Exception Logging (6 critical areas)
# ══════════════════════════════════════════════════════════════════════════════

# 1. waitlist auto-claim in cmd_book
old = "    except Exception:\n        pass\n    context.user_data.clear()\n    kb = ReplyKeyboardMarkup(\n        [[BTN_HAS_CARD_YES, BTN_HAS_CARD_NO], [BTN_CANCEL]],\n        resize_keyboard=True, one_time_keyboard=True,\n    )\n    await update.message.reply_text(\n        _step_hdr(1, 9, \"Member Card\") +"
new = "    except Exception as e:\n        logging.error(\"cmd_book: waitlist auto-claim failed: %s\", e)\n    context.user_data.clear()\n    kb = ReplyKeyboardMarkup(\n        [[BTN_HAS_CARD_YES, BTN_HAS_CARD_NO], [BTN_CANCEL]],\n        resize_keyboard=True, one_time_keyboard=True,\n    )\n    await update.message.reply_text(\n        _step_hdr(1, 9, \"Member Card\") +"
if old in content:
    content = content.replace(old, new, 1)
    print("OK wl_claim")
else:
    print("MISS wl_claim")

# 2. waitlist reserved_until parse
old = "                        except Exception:\n                            pass\n                    await update.message.reply_text("
new = "                        except Exception as e:\n                            logging.warning(\"waitlist reserved_until parse failed: %s\", e)\n                    await update.message.reply_text("
if old in content:
    content = content.replace(old, new, 1)
    print("OK wl_reserved")
else:
    print("MISS wl_reserved")

# 3. persist_sent_sets
old = "    except Exception:\n        pass\n\n_reminders_sent, _checkins_sent = _load_sent_sets()"
new = "    except Exception as e:\n        logging.warning(\"Failed to persist sent reminder/checkin IDs: %s\", e)\n\n_reminders_sent, _checkins_sent = _load_sent_sets()"
if old in content:
    content = content.replace(old, new, 1)
    print("OK persist_sent")
else:
    print("MISS persist_sent")

# 4. load_sent_sets
old = "    try:\n        with open(_SENT_FILE) as f:\n            d = json.load(f)\n        return set(d.get(\"reminders\", [])), set(d.get(\"checkins\", []))\n    except Exception:\n        return set(), set()"
new = "    try:\n        with open(_SENT_FILE) as f:\n            d = json.load(f)\n        return set(d.get(\"reminders\", [])), set(d.get(\"checkins\", []))\n    except Exception as e:\n        logging.warning(\"Failed to load sent reminder/checkin IDs from %s: %s\", _SENT_FILE, e)\n        return set(), set()"
if old in content:
    content = content.replace(old, new, 1)
    print("OK load_sent")
else:
    print("MISS load_sent")

# 5. startup booking re-queue time parse
old = "            except Exception:\n                pass\n        if requeued:"
new = "            except Exception as e:\n                logging.warning(\"startup booking re-queue time parse failed for bk #%s: %s\", bk.get(\"id\"), e)\n        if requeued:"
if old in content:
    content = content.replace(old, new, 1)
    print("OK startup_requeue")
else:
    print("MISS startup_requeue")

# 6. booking duplicate check API
old = "    except Exception:\n        existing = []\n\n    bk_date = d.get(\"bk_date\", \"\")"
new = "    except Exception as e:\n        logging.error(\"Booking duplicate check API failed for uid=%s: %s\", uid, e)\n        existing = []\n\n    bk_date = d.get(\"bk_date\", \"\")"
if old in content:
    content = content.replace(old, new, 1)
    print("OK dup_check")
else:
    print("MISS dup_check")

# ══════════════════════════════════════════════════════════════════════════════
# TASK 6: Cache Pruning Sweeper — insert after _cache_pop, before _split_message
# ══════════════════════════════════════════════════════════════════════════════
old = "def _cache_pop(key: str):\n    # Thread/async-safe pop with lock\n    with _CACHE_LOCK:\n        return _CACHE.pop(key, None)\n\n\ndef _split_message(text: str, limit: int = 4000) -> list[str]:"
new = "def _cache_pop(key: str):\n    # Thread/async-safe pop with lock\n    with _CACHE_LOCK:\n        return _CACHE.pop(key, None)\n\n\nasync def _async_cache_sweeper():\n    \"\"\"Background task: prune expired cache entries every 300 seconds (5 min).\n    Prevents unbounded memory growth from stale cached data.\"\"\"\n    await asyncio.sleep(30)  # initial delay to let bot stabilise\n    while not _shutdown_event.is_set():\n        try:\n            now = time.time()\n            with _CACHE_LOCK:\n                expired = [\n                    key for key, entry in _CACHE.items()\n                    if (now - entry[\"ts\"]) >= entry.get(\"ttl\", _CACHE_TTL)\n                ]\n                for key in expired:\n                    del _CACHE[key]\n            if expired:\n                logging.debug(\"Cache sweeper: pruned %d expired entries: %s\", len(expired), expired)\n        except Exception as e:\n            logging.warning(\"Cache sweeper error: %s\", e)\n        try:\n            await asyncio.wait_for(_shutdown_event.wait(), timeout=300)\n            logging.info(\"Cache sweeper: shutdown signal received, stopping\")\n            break\n        except asyncio.TimeoutError:\n            continue\n\n\ndef _split_message(text: str, limit: int = 4000) -> list[str]:"
if old in content:
    content = content.replace(old, new, 1)
    print("OK sweeper_func")
else:
    print("MISS sweeper_func")

# Register sweeper in _post_init
old = "        asyncio.create_task(_cache_invalidation_listener())\n        logging.info(\"Booking scheduler started | Cache listener started | Commands registered\")"
new = "        asyncio.create_task(_cache_invalidation_listener())\n        asyncio.create_task(_async_cache_sweeper())\n        logging.info(\"Booking scheduler started | Cache listener started | Cache sweeper started | Commands registered\")"
if old in content:
    content = content.replace(old, new, 1)
    print("OK sweeper_reg")
else:
    print("MISS sweeper_reg")

# Write
with open(filepath, "w") as f:
    f.write(content)

print(f"Final length: {len(content)}, lines: {content.count(chr(10))}")
print("DONE: All Phase 2 modifications applied to customer_bot.py")
