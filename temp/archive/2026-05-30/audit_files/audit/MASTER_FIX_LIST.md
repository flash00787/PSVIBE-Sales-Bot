# PS VIBE — Master Fix List
**Generated:** 2026-05-28 12:20 UTC
**Source:** 11 audit reports from comprehensive bot/system audit

---

## 🔴 CRITICAL (Must Fix Immediately)

### Security (2 issues)

| # | Issue | Severity | Effort | Report |
|---|---|---|---|---|
| S-1 | **MySQL port 3306 EXPOSED to internet** — anyone can brute-force | 🔴 CRITICAL | 5 min | `mysql_security.md` |
| S-2 | **MySQL passwords visible** via `docker inspect psvibe-mysql` | 🔴 CRITICAL | 15 min | `mysql_security.md` |
| S-3 | `service_account.json` world-readable (chmod 644) | 🟡 HIGH | 1 min | `mysql_security.md` |
| S-4 | `analytics.py` + `dashboard_bot.py` world-writable (chmod 666) | 🟡 HIGH | 1 min | `mysql_security.md` |
| S-5 | MySQL Docker binds to `0.0.0.0` not `127.0.0.1` | 🟡 HIGH | 10 min | `mysql_security.md` |

### Customer Bot (6 issues)

| # | Issue | Severity | Effort | Report |
|---|---|---|---|---|
| CB-1 | **12 API endpoint paths WRONG** — all return 404 (e.g. `sheets/game-library` → `fetch_games`) | 🔴 CRITICAL | 1-2 hrs | `customer_bot_audit.md` + `customer_bot_fix_plan.md` |
| CB-2 | **API response format unwrap MISSING** — bot doesn't extract `response.data` | 🔴 CRITICAL | 30 min | `customer_bot_fix_plan.md` |
| CB-3 | **`booking.py` MISSING** — 3 command handlers (`/mybookings`, `/refer`, `/waitlist`) crash on call | 🔴 CRITICAL | 3-4 hrs | `customer_bot_fix_plan.md` |
| CB-4 | **16 booking conversation states STUBBED** — every state = `lambda u,c: None` | 🔴 CRITICAL | 3-4 hrs | `customer_bot_fix_plan.md` |
| CB-5 | **`fetch_members` returns flat ID list** — bot expects `[{member_id, name, phone}]` | 🟠 HIGH | 1-2 hrs | `customer_bot_fix_plan.md` |
| CB-6 | **Feedback callback pattern MISMATCH** — `^fb:comment_prompt:` vs actual `^fbc:` | 🟠 HIGH | 30 min | `customer_bot_fix_plan.md` |

### Sales Bot (3 issues)

| # | Issue | Severity | Effort | Report |
|---|---|---|---|---|
| SB-1 | **10 write functions BYPASS API** — `create_booking`, `end_booking`, `save_attendance`, `add_console_game`, `remove_console_game`, `update_game_library_install`, `add_console_to_setting`, `remove_console_from_setting`, `set_game_disc_count`, `cancel_booking` write directly to gspread | 🔴 HIGH | 1-2 hrs | `sales_bot_api_sheet.md` |
| SB-2 | **BotState class name COLLISION** — `@dataclass BotState` conflicts with `class BotState(IntEnum)` | 🟡 MEDIUM | 1 hr | `sales_bot_completeness.md` |
| SB-3 | **`bot/keep_alive.py` dead code** — never imported | 🟡 MEDIUM | 10 min | `sales_bot_completeness.md` |

### API Server (1 issue)
| # | Issue | Severity | Effort | Report |
|---|---|---|---|---|
| API-1 | **6 analytics endpoints return 500** — `dashboard`, `daily_sales`, `topups`, `weekly_trends`, `member_activity`, `console_usage` | 🟡 MEDIUM | 2-4 hrs | `sales_bot_api_smoke.md` |

---

## 🟠 HIGH PRIORITY

### Backend Endpoints to Create (7 new)

| # | Endpoint | Method | Needed For | Effort |
|---|---|---|---|---|
| BE-1 | `/api/sheets/settings/contacts` | GET | Customer bot contacts feature | 1 hr |
| BE-2 | `/api/bookings?telegramChatId=X` | GET | Customer bot booking lookup | 2 hrs |
| BE-3 | `/api/bookings/{id}` | GET | Customer bot booking detail | 1 hr |
| BE-4 | `/api/bookings/{id}/status` | PATCH | Customer bot cancel booking | 1 hr |
| BE-5 | `/api/feedback` | POST | Customer bot feedback feature | 1 hr |
| BE-6 | `/api/sheets/log` | POST | Customer bot query logging | 30 min |
| BE-7 | `/api/bot-users/track` | POST | Customer bot usage tracking | 30 min |

### Data Model Enhancements

| # | Change | Why | Effort |
|---|---|---|---|
| DM-1 | Add `telegramChatId` column to `Console_Booking` sheet | Customer bot needs to query user's bookings | 30 min |
| DM-2 | Create feedback sheet (or append to existing) | Customer bot feedback storage | 30 min |
| DM-3 | Enhance `fetch_members` to return full member objects (not just ID list) | Customer bot needs member details | 2 hrs |

### API Fixes (16 broken endpoints)

| # | Endpoint | Issue | Fix |
|---|---|---|---|
| AE-1 | `fetch_consoles_with_game` | 404 Not Found | Check route registration in app.py |
| AE-2 - AE-7 | 6 analytics endpoints | 500 Internal Error | Debug analytics logic (probably bad sheet refs) |
| AE-8 | `fetch_member_data/{id}` | 404 for ID 1 | Accept string IDs or numeric |
| AE-9 | `fetch_wallet_mins/{id}` | 404 for ID 1 | Same as AE-8 |
| AE-10 | `fetch_balance_mins/{id}` | 500 for ID 1 | Member not found handler |
| AE-11 | `fetch_member_tier/{id}` | 404 for ID 1 | Same as AE-8 |
| AE-12 | `fetch_console_multiplier/{id}` | 500 | Missing try/except for unknown console |
| AE-13 | `fetch_member_effective_rate/{id}` | 404 for ID 1 | Same as AE-8 |
| AE-14 | `fetch_referral_code/{id}` | 404 for ID 1 | Same as AE-8 |
| AE-15 | `end_booking/{id}` | 405 Method Not Allowed | Currently GET → change to POST |
| AE-16 | `cancel_booking/{id}` | 405 Method Not Allowed | Currently GET → change to POST |
| AE-17 | `remove_console_from_setting/{id}` | 405 Method Not Allowed | Currently GET → change to POST |
| AE-18 | `save_attendance` | 500 | Debug attendance save logic |

---

## 🟡 MEDIUM PRIORITY

### Code Cleanup

| # | Issue | File(s) | Effort |
|---|---|---|---|
| CC-1 | Remove dead import: `fcntl` | `bot/__init__.py` | 5 min |
| CC-2 | Remove dead import: `signal` | `bot/__init__.py` | 5 min |
| CC-3 | Remove dead import: `sys` | `app.py`, `keep_alive.py` | 5 min |
| CC-4 | Delete dead file `bot/keep_alive.py` | Entire file | 5 min |
| CC-5 | Rename `BotState` dataclass to `BotConfig` | `bot/__init__.py` | 30 min |
| CC-6 | Rename `AttendState` dataclass to `AttendConfig` | `bot/__init__.py` | 15 min |
| CC-7 | Remove unused environment variables from `.env` | — | 15 min |

### Customer Bot P2 Issues

| # | Issue | Fix | Effort |
|---|---|---|---|
| CP-1 | `BK_*` constants defined TWICE in `handlers.py` (lines 48-63 + 71-86) | Remove duplicate | 10 min |
| CP-2 | `/cancel` command double-registered (main.py + handlers.py) | Remove one registration | 10 min |
| CP-3 | `cmd_contacts` missing keyboard after send contact | Add inline keyboard | 15 min |

---

## 🟢 ENHANCEMENT SUGGESTIONS

### Architecture Improvements

| # | Suggestion | Rationale | Effort |
|---|---|---|---|
| EN-1 | Add `_HAS_API` gate to all 10 bypassed write functions | Ensures all writes go through API | 1-2 hrs |
| EN-2 | Add retry logic (`_SHEETS_RETRY_CODES`) to API client | Defensive against 429/500 | 1 hr |
| EN-3 | Add cache invalidation hook for API writes | Bot caches stale data after direct writes | 1 hr |
| EN-4 | Unify all sheet access through API (remove all direct gspread from handlers) | Single source of truth | 4-8 hrs |
| EN-5 | Add health check endpoint for customer bot | Proactive monitoring | 30 min |

### Feature Gaps

| # | Feature | Description | Priority |
|---|---|---|---|
| FG-1 | Customer bot booking flow (full) | 16 state booking conversation with member lookup, time picker, console selection | CRITICAL |
| FG-2 | Customer bot referral feature | Show referral code + program info | HIGH |
| FG-3 | Customer bot waitlist feature | Waitlist entry flow for fully-booked times | HIGH |
| FG-4 | Sales bot: N8N webhook integration for session end notification | Customer notified when session ends | MEDIUM |
| FG-5 | Sales bot: Low balance alert via Telegram | Customer notified when balance < threshold | MEDIUM |

---

## 📊 Fix Effort Summary

| Priority Category | Total Items | Estimated Total Effort |
|---|---|---|
| 🔴 CRITICAL (must fix) | 12 issues | ~15-20 hrs |
| 🟠 HIGH (should fix) | 18 issues | ~18-25 hrs |
| 🟡 MEDIUM (nice to fix) | 10 issues | ~3-4 hrs |
| 🟢 ENHANCEMENT | 7 items | ~15-20 hrs |
| **TOTAL** | **47 items** | **~51-69 hrs** |

## 🚨 NEW ISSUE FOUND (2026-05-28 12:25 UTC — Crash Analysis)

| # | Issue | Severity | Effort |
|---|---|---|---|
| IN-1 | **No systemd service files** — bots run via nohup, no auto-restart on crash | 🔴 CRITICAL | 30 min |
| IN-2 | **`start_bots_v3.sh` references OLD directory** `/root/Aung Chan Myint/Sales-Tele-Bot/` — broken path | 🟡 MEDIUM | 10 min |
| IN-3 | **Old crash in `/root/Sales-Tele-Bot/customer_bot.py`** — residual, directory gone | ✅ Already fixed | — |

## ✅ Priority Fix Order

**Updated approach:** Now that max agents = 20 (was 5), we can run FULL batches in parallel.

```
PHASE 1 — CRITICAL (immediate action, ~8 hrs total)
  ├── 🔒 Security: S-1, S-2, S-3, S-4, S-5 (35 min)
  ├── 🐛 Customer Bot API: CB-1, CB-2, CB-6 (2-3 hrs)
  ├── 🐛 Sales Bot: SB-1 (1-2 hrs)
  └── 🧹 Systemd services: IN-1, IN-2 (40 min)

PHASE 2 — BACKEND (~8 hrs total)
  ├── 🏗️ New endpoints: BE-1→7 (7 hrs)
  ├── 🔧 API fixes: AE-1→18 (6 hrs)
  └── 📊 Data model: DM-1, DM-2, DM-3 (3 hrs)

PHASE 3 — CUSTOMER BOT BOOKING (~8 hrs total)
  ├── 📝 Create booking.py: CB-3 (3-4 hrs)
  ├── 🎮 Implement 16 booking states: CB-4 (3-4 hrs)
  └── 🔗 Member data fix: CB-5 (1-2 hrs)

PHASE 4 — CLEANUP (~8 hrs total)
  ├── 🧹 Code cleanup: CC-1→7 (1 hr)
  ├── 🏗️ Architecture: EN-1→5 (8 hrs)
  └── ⭐ Feature gaps: FG-1→5 (10 hrs)
```
