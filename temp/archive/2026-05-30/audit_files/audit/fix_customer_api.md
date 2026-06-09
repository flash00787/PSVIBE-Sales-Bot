# Fix Customer Bot API Paths + Response Unwrap (CB-1, CB-2)

**Date:** 2026-05-28  
**File:** `/home/node/.openclaw/workspace/psvibe_customer_src/customer_bot/api.py`

## Changes Applied

### 1. API Path Fixes

| Function | Old Path | New Path |
|---|---|---|
| `_fetch_games_full()` | `sheets/game-library` | `fetch_games` |
| `_fetch_members()` | `sheets/members-list` | `fetch_members` |
| `_fetch_consoles()` | `sheets/consoles` | `fetch_console_status` |
| `_fetch_promotions()` | `sheets/promotions` | `fetch_promotions_cached` |
| `_fetch_sales_data()` | `sheets/sales-summary` | `analytics/daily_sales` |

### 2. Response Unwrapping

Each `_fetch_*` function now unwraps the API response:

```python
# Before:
data = await _api_get("old-path")

# After:
raw = await _api_get("new-path")
data = raw.get("data", {}) if isinstance(raw, dict) else raw
```

This handles the new API format where data is nested under a `"data"` key.

### 3. Unchanged (correct as-is)

| Function | Path | Status |
|---|---|---|
| `_fetch_config()` | `sheets/config` | ✅ kept |
| `_fetch_contacts()` | `sheets/settings/contacts` | ✅ kept |
| `log_to_sheet()` | `sheets/log` | ⚠️ placeholder (needs new endpoint) |
| `track_usage()` | `bot-users/track` | ⚠️ placeholder (needs new endpoint) |

### 4. Pending: Placeholders

`log_to_sheet` and `track_usage` still use old paths (`sheets/log`, `bot-users/track`) as placeholders. These need new API endpoints defined before they can be fixed.

## Deployment Note

The fixed file is at: `/home/node/.openclaw/workspace/api_customer_fixed.py`

**Cannot overwrite the original directly** — the source directory is root-owned. Deploy with:

```bash
sudo cp /home/node/.openclaw/workspace/api_customer_fixed.py \
  /home/node/.openclaw/workspace/psvibe_customer_src/customer_bot/api.py
```

Or on the VPS (`5.223.81.16`):
```bash
scp api_customer_fixed.py root@5.223.81.16:/root/psvibe-sale-bot/customer_bot/api.py
```

## Diff Summary

- **Lines changed:** 10 insertions (+5 `raw =` lines, +5 `data = raw.get(...)` lines)
- **Lines modified:** 5 `_api_get()` call lines
- **Net lines:** +5 (431 vs 426 in original)
