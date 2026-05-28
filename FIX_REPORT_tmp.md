# Personal-Wallet-Tele-Bot — Fix Report

**Date:** 2026-05-27 21:50 UTC  
**VPS:** 5.223.81.16 (openClawAgent)  
**Fixed by:** OpenClaw Subagent

---

## Executive Summary

The bot is **running** on `psvibe-wallet.service`. Telegram API connectivity, Flask keep-alive (port 5001), and all Python code are syntactically correct. **One critical issue** remains that requires a manual action: the Google Sheets service account needs to be granted access to the target spreadsheet.

---

## Issues Found & Fixed

### 1. ✅ FIXED: Empty PermissionError Messages (Code Fix)

**Severity:** Medium (diagnostic / UX)  
**Status:** ✅ **RESOLVED** (code patch applied to `main.py`)

**Problem:** gspread's `PermissionError` on `open_by_key()` returns an empty message (`PermissionError()` with no args). The bot logged:
```
Cache warmer [settings] failed: 
```
with nothing after the colon, making it impossible to diagnose from logs.

**Fix applied (2 patches to `main.py`):**

1. **`_gsheet_retry` decorator (line ~311):** Added explicit PermissionError detection that wraps the empty error with a clear message:
```python
if isinstance(exc, PermissionError) or "PermissionError" in type(exc).__name__:
    raise PermissionError(
        "Service account does not have access to the Google Sheet. "
        "Share the sheet with the SA email as Editor."
    )
```

2. **`_err()` function (line ~430):** Added handling for empty exception messages:
```python
if not msg:
    if isinstance(exc, PermissionError) or type(exc).__name__ == "PermissionError":
        msg = "Permission denied - the service account does not have access to this Google Sheet. Share the sheet with the SA email as Editor."
    else:
        msg = f"{type(exc).__name__} (no details)"
```

**Result:** Logs now show a clear, actionable message instead of an empty string.

---

### 2. ⚠️ REQUIRES MANUAL ACTION: Google Sheets Permission

**Severity:** CRITICAL  
**Status:** ⚠️ **REQUIRES MANUAL ACTION**

**Problem:** The service account used by the bot does NOT have access to the target Google Sheet. All 6 cache warmer tasks (settings, account_balances, tx_rows, opening_balances, fx_rates, monthly_summary) fail with PermissionError on every cycle.

**Affected Service Account:**
- **Email:** `user-408@ps-vibe-sales-tele-bot.iam.gserviceaccount.com`
- **Project:** `ps-vibe-sales-tele-bot`
- **SA JSON file:** `/root/Personal-Wallet-Tele-Bot/bot/service_account.json`

**Target Spreadsheet:**
- **Sheet ID:** `1mlc9AmhwIVCk7egJoQgX4ld6z9kpwciDegxYA8_BPRc`

**How to fix (manual steps):**
1. Open the Google Sheet in a browser:
   - https://docs.google.com/spreadsheets/d/1mlc9AmhwIVCk7egJoQgX4ld6z9kpwciDegxYA8_BPRc
2. Click **Share** (top-right)
3. Add this email as **Editor**:
   - `user-408@ps-vibe-sales-tele-bot.iam.gserviceaccount.com`
4. Click **Send** (no notification needed — it's a service account)
5. The bot's cache warmer will auto-recover on its next cycle (~90 seconds)

**Required Worksheets in the Sheet:**
- `Settings` — Account list, categories, projects, exchange rates
- `Transaction_Log` — All transactions (columns: Date, Type, Category, AccountFrom, AccountTo, Amount, Project, Scope)
- `Opening_Balances` — Initial balances (columns: Date, Type, Entity, Amount, Notes)
- `Saas_Tracker` — SaaS subscriptions list

**Note:** The Sales-Tele-Bot service account was used here (`user-408@ps-vibe-sales-tele-bot.iam.gserviceaccount.com`). This is the SAME SA — both bots share it. The Sales-Tele-Bot works because its sheet IS shared with this SA, but the Personal-Wallet-Tele-Bot sheet is NOT.

---

## Verification Results

### ✅ Working
| Check | Status | Detail |
|-------|--------|--------|
| Python syntax (all .py files) | ✅ OK | `python3 -m py_compile` passes on all files |
| Bot imports | ✅ OK | `telegram`, `gspread`, `google.oauth2`, `flask`, all import successfully |
| Service running | ✅ OK | `psvibe-wallet.service`: active (running) |
| Auto-start on boot | ✅ OK | Service enabled |
| Telegram API (getMe) | ✅ OK | 200 OK |
| Bot commands | ✅ OK | setMyCommands 200 OK |
| Polling (getUpdates) | ✅ OK | 200 OK, receiving updates |
| Flask keep-alive | ✅ OK | Port 5001, `/ping` → 200 "pong", `/` → HTML status page |
| Webhook routes | ✅ OK | `/refresh`, `/notify`, `/daily-summary`, `/remind`, `/monthly-report`, `/api/today` |
| gspread auth | ✅ OK | Credentials load and authenticate successfully |
| Log rotation | ✅ OK | RotatingFileHandler (5 MB × 3 backups) |
| Error messages | ✅ FIXED | Clear PermissionError messages in logs |

### ⚠️ Blocked
| Check | Status | Detail |
|-------|--------|--------|
| Google Sheets access | ⚠️ Permission denied | SA needs Editor access (see manual fix above) |
| Cache warmers (×6) | ⚠️ All fail | Depend on Sheets access |
| Transaction logging | ⚠️ Will fail | Users cannot log transactions until Sheets access is granted |
| All /commands using data | ⚠️ Will fail | `/balance`, `/accounts`, `/summary`, `/debts`, `/networth`, `/fx`, `/saas`, `/project`, `/split`, `/monthly`, `/weekly` all depend on Sheets data |

---

## Systemd Service Status

```
Service:     psvibe-wallet.service
Status:      active (running)
Enabled:     yes (auto-start on boot)
ExecStart:   /root/Personal-Wallet-Tele-Bot/bot/venv/bin/python3 main.py
WorkDir:     /root/Personal-Wallet-Tele-Bot/bot/
Restart:     on-failure (5s delay)
User:        root
PID:         185811
Memory:      69.1M
```

---

## Directory Structure (Post-Fix)

```
/root/Personal-Wallet-Tele-Bot/
├── bot/
│   ├── main.py              (246 KB — patched)
│   ├── keep_alive.py         (15 KB)
│   ├── requirements.txt
│   ├── vps_setup.sh
│   ├── service_account.json  (user-408@ps-vibe-sales-tele-bot)
│   ├── .env
│   ├── bot_status.log        (rotating, 5 MB × 3)
│   ├── bot.lock              (PID lock file)
│   └── venv/                 (Python 3.12)
├── start_wallet_bot.sh
└── FIX_REPORT.md             (this file)
```

---

## Action Items for Resolution

1. **🔴 CRITICAL — Immediate:** Share the Google Sheet `1mlc9AmhwIVCk7egJoQgX4ld6z9kpwciDegxYA8_BPRc` with `user-408@ps-vibe-sales-tele-bot.iam.gserviceaccount.com` as **Editor**
2. **🟡 Optional:** Consider creating a dedicated service account for the Personal-Wallet-Tele-Bot (separate from Sales-Tele-Bot) for better security isolation
3. **🟡 Optional:** Remove the Telegram bot token from log files (currently visible in `bot_status.log` entries for HTTP requests)
4. **🟢 Verified:** No code changes needed beyond the 2 patches already applied
