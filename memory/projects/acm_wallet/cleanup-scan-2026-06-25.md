# ACM Wallet Cleanup Scan — 2026-06-25

Post-migration (Google Sheets → MySQL) comprehensive leftover scan and cleanup.

## Scan Results

### 1. STALE FILES
| File | Status | Action |
|------|--------|--------|
| `bot/service_account.json` | 2387 bytes, last used May 2 | ✅ REMOVED |
| `bot/main.py.bak-20260625-phase1` | 246KB, Jun 25 05:01 | ✅ REMOVED |
| `bot/main.py.bak-phase2` | 249KB, Jun 25 05:09 | ✅ REMOVED |

### 2. STALE IMPORTS / CODE
- `from dotenv import load_dotenv` — **KEPT** (still needed for .env loading)
- `load_dotenv(...)` — **KEPT** (reads DB_BACKEND from .env)
- No gspread, oauth2, google-auth, SCOPES, Credentials imports — clean ✅
- No `.append_row`, `.col_values`, `_sheet_client`, `_gsheet_retry` calls — clean ✅
- `_SHEETS_TIMEOUT` → **RENAMED** to `_DB_TIMEOUT` ✅
- 26 Phase 2 comment lines → **ALL REMOVED** ✅

### 3. REQUIREMENTS
- `gspread`, `google-auth`, `oauth2client` — not present ✅
- `mysql-connector-python>=8.0` — present ✅
- `pyasn1==0.6.3`, `pyasn1_modules==0.4.2` — **REMOVED** (stale google-auth transitive deps) ✅

### 4. DATABASE HEALTH
All 7 tables present and healthy:
| Table | Rows | Indexes |
|-------|------|---------|
| budgets | 0 | PRIMARY(id), idx_user_scope(user_id, scope) |
| fx_rates | 4 | PRIMARY(id), currency, idx_currency |
| opening_balances | 44 | PRIMARY(id), idx_entity, idx_type |
| reminders | 0 | PRIMARY(id), idx_user |
| saas_subscriptions | 1 | PRIMARY(id) |
| settings | 56 | PRIMARY(id), uk_type_name(type, name) |
| transactions | 147 | PRIMARY(id), idx_date, idx_type, idx_category, idx_scope, idx_acc_from, idx_acc_to |

### 5. BOT HEALTH
- Restarted at 06:39 UTC with cleaned code — **no errors** ✅
- Prior instance had a `NameError: name 'budgets' is not defined` (PID 2254772 at 06:28) — resolved after restart, no recurrence.
- Flask dev server warning (normal — UptimeRobot keep-alive only)

### 6. CONVERSATION STATE
- `conversation_state.pkl` (243 bytes) — **KEPT** (PicklePersistence for ConversationHandler state, NOT data storage)
- PicklePersistence still active in code — Expected ✅

### 7. BACKUP STRATEGY
- No mysqldump cron existed → **ADDED** daily at 3:00 AM UTC:
  ```
  0 3 * * * mysqldump ... acm_wallet | gzip > /root/backups/db/acm_wallet/acm_wallet_$(date +%Y%m%d).sql.gz
  ```
- Retain 30 days, auto-cleanup recommended (add `find ... -mtime +30 -delete` later)

### 8. YYO WALLET — SHARED SHEET CHECK
- YYO Wallet STILL uses sheet `1QZGF1shzgSFdaQR-S81wLJ_-yQj6Nyy8pM5ayB32ZcM`
- ⚠️ **DO NOT DELETE** the Google Sheet — YYO Wallet still depends on it!
- ACM Wallet's `DB_BACKEND=mysql` is fully independent now.

### 9. ENV CLEANUP
- No `SHEET_ID` or `SPREADSHEET` vars present ✅
- `DB_BACKEND=mysql` set ✅
- Old Google Sheets comments → **CLEANED** ✅

## Cleanup Actions Performed

1. ✅ Removed `service_account.json` from ACM wallet
2. ✅ Removed 2 `.bak` backup files (phase1 and phase2)
3. ✅ Renamed `_SHEETS_TIMEOUT` → `_DB_TIMEOUT` in main.py (lines 275, 281)
4. ✅ Deleted all 26 stale Phase 2 comment lines
5. ✅ Added daily mysqldump cron at 03:00 UTC → `/root/backups/db/acm_wallet/`
6. ✅ Removed `pyasn1`, `pyasn1_modules` from requirements.txt
7. ✅ Cleaned `.env` — removed Google Sheets references from comments
8. ✅ Bot restarted successfully — running clean, no errors

## Remaining Notes

- `pyasn1`/`pyasn1_modules` remain installed system-wide (needed by YYO wallet's google-auth)
- `PicklePersistence` remains for ConversationHandler state (by design)
- `conversation_state.pkl` is 243 bytes — healthy size for conversation state only
- Bot uses `venv` at `/root/ACM-Personal-Wallet/bot/venv/`
- Keep-alive Flask runs on port 5001
