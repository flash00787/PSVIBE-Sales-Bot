#!/usr/bin/env python3
"""Fix _tg_send retry logic — was missed due to unicode em dash char."""
filepath = "/root/Sales-Tele-Bot_staging/customer_bot.py"
with open(filepath, "r") as f:
    content = f.read()

print(f"Current length: {len(content)}")

# _tg_send with actual em dash character
old = "def _tg_send(body: dict):\n    import urllib.error\n    data = json.dumps(body).encode()\n    r = _req.Request(\n        f\"https://api.telegram.org/bot{CUSTOMER_BOT_TOKEN}/sendMessage\",\n        data=data, headers={\"Content-Type\": \"application/json\"}, method=\"POST\",\n    )\n    try:\n        with _req.urlopen(r, timeout=15) as resp:\n            return json.loads(resp.read())\n    except urllib.error.HTTPError as e:\n        detail = e.read().decode(errors=\"replace\")\n        logging.error(\"tg_send HTTP %s \u2014 %s\", e.code, detail)\n        return None\n    except Exception as e:\n        logging.warning(\"tg_send failed: %s\", e)\n        return None"

new = "def _tg_send(body: dict):\n    import urllib.error as _urlerr\n    import http.client as _http\n    data = json.dumps(body).encode()\n    r = _req.Request(\n        f\"https://api.telegram.org/bot{CUSTOMER_BOT_TOKEN}/sendMessage\",\n        data=data, headers={\"Content-Type\": \"application/json\"}, method=\"POST\",\n    )\n    for attempt in range(4):  # 1 initial + 3 retries\n        try:\n            with _req.urlopen(r, timeout=15) as resp:\n                return json.loads(resp.read())\n        except _urlerr.HTTPError as e:\n            detail = e.read().decode(errors=\"replace\")\n            logging.error(\"tg_send HTTP %s \u2014 %s\", e.code, detail)\n            return None\n        except (_urlerr.URLError, TimeoutError, ConnectionError,\n                _http.HTTPException, OSError) as e:\n            if attempt < 3:\n                delay = 2 ** attempt\n                logging.warning(\"tg_send attempt %d/4 failed (retry in %ds): %s\", attempt + 1, delay, e)\n                time.sleep(delay)\n            else:\n                logging.error(\"tg_send FAILED after 4 attempts: %s\", e)\n                return None\n        except Exception as e:\n            logging.warning(\"tg_send failed: %s\", e)\n            return None\n    return None"

if old in content:
    content = content.replace(old, new, 1)
    print("OK _tg_send fixed")
else:
    # Try with exact repr
    import re
    # Find _tg_send in the file
    idx = content.find("def _tg_send(body: dict):")
    if idx >= 0:
        snippet = content[idx:idx+600]
        print("Found at:", idx)
        print("Snippet:", repr(snippet[:200]))
        # Just try matching with \u2014 replaced literally
        old2 = old.replace("\u2014", "\u2014")  # ensure it's the same
        if old2 in content:
            content = content.replace(old2, new, 1)
            print("OK _tg_send fixed (alt)")
        else:
            print("STILL MISS")
            print("old repr:", repr(old))
    else:
        print("NOT FOUND _tg_send at all!")

with open(filepath, "w") as f:
    f.write(content)

print("DONE")
