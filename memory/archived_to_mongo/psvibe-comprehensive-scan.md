# PS VIBE — Comprehensive Project Scan
**Date:** 2026-07-01 | **Scanner:** Kora Subagent (DeepSeek V4 Pro)  
**Scope:** All 4 codebases — API Server, Sales Bot, Web Dashboard, Discord Bot

---

## 🔴 CRITICAL BUGS & VULNERABILITIES

### 1. Hardcoded Discord Bot Token Exposed in Source Code
- **Severity:** 🔴 CRITICAL
- **File:** `/root/psvibe-discord-bot/bot.js:14`
- **Finding:** Discord bot token `MTUxNjEyMDQwODM5MzUxNTA4MQ.GUNnQ9.jc9OcTo4Zz1hCbUoQJqijLReg_YBSFCY89y8ys` is hardcoded directly in source code. This token grants full control of the Discord bot and can be used by anyone who has access to the codebase to impersonate the bot, send messages, access channels, etc.
- **Fix:** Move to environment variable: `process.env.DISCORD_BOT_TOKEN`. Rotate token immediately via Discord Developer Portal.

### 2. Hardcoded API Key Exposed in Discord Bot
- **Severity:** 🔴 CRITICAL
- **File:** `/root/psvibe-discord-bot/bot.js:15`
- **Finding:** PS VIBE API key `JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ` hardcoded. Anyone with this key can call all API endpoints authenticated, including member data, wallet operations, bookings, inventory.
- **Fix:** Use environment variable. Rotate API key.

### 3. Hardcoded MySQL Password in Source Code
- **Severity:** 🔴 CRITICAL
- **File:** `/root/psvibe_api_server/mysql_db.py:7`
- **Finding:** Database password `PsVibe@2026_Rotated!` hardcoded in source with full credentials (host, user, password, database name). If source ever leaks, attacker has full DB access.
- **Fix:** Move all DB credentials to environment variables or a secure config file with restricted permissions (0600).

### 4. Discord Bot Uses Root MySQL with Empty Password
- **Severity:** 🔴 CRITICAL
- **File:** `/root/psvibe-discord-bot/bot.js:58`
- **Finding:** `mysql.createPool({ host:'localhost', user:'root', password:'', database:'psvibe_api' })` — MySQL root user with NO password. This is dangerous: if the bot is compromised, the attacker gets root DB access.
- **Fix:** Create dedicated MySQL user with minimal privileges. NEVER use root with empty password.

### 5. Default Admin Password in Auth Module
- **Severity:** 🔴 HIGH
- **File:** `/root/psvibe_api_server/auth.py:63-69`
- **Finding:** Auto-creates default admin user with password `admin123` if dashboard_users table is empty. This is a well-known default credential and trivial to guess. The auto-creation silently happens on first credential load.
- **Fix:** (a) Remove auto-creation OR (b) Generate random password and log it once, or (c) Require setup script to be run manually. At minimum, use a stronger random password.

### 6. JWT Secret Has Weak Fallback
- **Severity:** 🟠 HIGH
- **File:** `/root/psvibe_api_server/auth.py:16`
- **Finding:** `SECRET_KEY = os.getenv("JWT_SECRET_KEY", "psvibe-dashboard-secret-key-2026")` — if JWT_SECRET_KEY env var is not set, the fallback is a predictable string. Anyone who knows this can forge valid JWT tokens.
- **Fix:** Remove fallback; require the env var to be set. Generate with `openssl rand -hex 32`.

### 7. Unauthenticated Webhook Endpoints
- **Severity:** 🟠 HIGH
- **File:** `/root/psvibe_api_server/app.py:737, 750`
- **Finding:** `/webhook/booking-reminder` and `/webhook/booking-reminder/cancel` have NO authentication. Anyone can call these to manipulate booking reminders.
- **Fix:** Add API key verification OR HMAC signature verification to webhook endpoints.

### 8. Unauthenticated API Endpoints (Multiple)
- **Severity:** 🟠 HIGH
- **Files:** `/root/psvibe_api_server/app.py:320, 424-425, 447, 457, 3380-3400, 4150+`
- **Finding:** Several endpoints have no authentication check:
  - `/api/debug_auth` (line 320) — exposes API key in response
  - `/kora`, `/kora/{path:path}` (line 424-425) — Kora dashboard proxy
  - `/api/health` (line 447) — acceptable, public health check
  - `/api/mysql/health` (line 457) — exposes DB health
  - `/api/receipt/{voucher_id}` (line 3380) — anyone can fetch receipts with path
  - `/currency-exchange/api-proxy/{path}` (line 4150+) — SEL API proxy
  - Multiple static file/dashboard routes
- **Fix:** Review each endpoint. Add auth where needed. Health check is fine without auth. Receipt endpoint should at minimum validate the voucher_id format.

### 9. Bare `except:` Blocks (28+ occurrences — error swallowing)
- **Severity:** 🔴 CRITICAL
- **Files:** `app.py` (16+), `dashboard_routes.py` (7), `patch_routes.py` (5), `sync_settings_to_mysql.py` (3), `gsheet_to_mysql.py` (1)
- **Finding:** Bare `except:` without `except Exception as e` catches KeyboardInterrupt, SystemExit, and other critical exceptions. This makes the process unkillable with Ctrl+C in some contexts and silently swallows real bugs.
  - `app.py:2842` — `except: pass` — completely silent error swallowing
  - `app.py:2953` — `except: pass` — completely silent error swallowing
  - `sync_settings_to_mysql.py:25, 32` — `except: return 0` and `except: return 0.0`
- **Fix:** Replace ALL bare `except:` with `except Exception as e:` and log the error. Never use `except: pass`.

### 10. N+1 Query Pattern in Member Fetch
- **Severity:** 🟠 HIGH
- **File:** `/root/psvibe_api_server/app.py:770-780`
- **Finding:** `_calc_member_liability_kyat()` performs separate queries per member. When `api_fetch_members` is called, it iterates over all members and calls this for each one, creating N+1 queries.
- **Fix:** Batch the FIFO calculation with a single JOIN query or pre-load all top-up logs.

### 11. Race Condition — No Transaction on Status Updates
- **Severity:** 🟠 HIGH
- **Files:** `/root/psvibe_api_server/app.py:177, 182, 190, 195, 207, 212`
- **Finding:** Multiple `UPDATE console_status` operations in `_sync_console_status` are not wrapped in a transaction. If two concurrent operations change the same console, data corruption is possible (e.g., two check-ins on the same console).
- **Fix:** Wrap critical UPDATE sequences in `START TRANSACTION / COMMIT` blocks.

### 12. Race Condition — `SELECT ... FOR UPDATE` Availability Check
- **Severity:** 🟡 MEDIUM
- **File:** `/root/psvibe_api_server/app.py:3051`
- **Finding:** The `FOR UPDATE` in the availability query is inside a SELECT, but the actual INSERT/UPDATE that follows is not in the same transaction. Between the check and the write, another request could have changed the state.
- **Fix:** Wrap the entire check-and-write sequence in a transaction.

### 13. SQL Injection Risk via Dynamic SQL
- **Severity:** 🟠 HIGH
- **File:** `/root/psvibe_api_server/app.py:1658, 1662, 3554-3556, 3710`
- **Finding:** F-string building of SQL in several places:
  - `_allowed_from` tuple is injected via f-string into UPDATE (line 1658)
  - Column names built from dict keys in `customer_bot_users` upsert (line 3554)
  - Date string `since` interpolated directly into WHERE clause (line 3710)
  - `console_ids` built into `{_placeholders}` (line 3051)
- **Fix:** All of these use f-strings to inject values that come from Python variables, not user input directly, so the risk varies:
  - Lines 3554-3556: Column names from code dict — acceptable if keys are controlled
  - Line 3710: `since` date parameter — **SHOULD use parameterized query**
  - Lines 1658/1662: `_allowed_from` — if controlled, fine, but better to parameterize

### 14. Timezone Mixing (MMT vs UTC)
- **Severity:** 🟡 MEDIUM
- **Files:** `/root/psvibe_api_server/app.py` (multiple), `analytics.py:29`
- **Finding:** MMT timezone is used in some places (`datetime.now(MMT)`), UTC in others (`datetime.now(timezone.utc)`), and bare `datetime.now()` (system local) in at least one place (`app.py:3585`). MySQL uses `NOW()` which returns server time. This mixing can cause off-by-6.5-hour bugs in booking times, reports, and analytics.
  - `analytics.py:29` — uses MMT
  - `app.py:366` — `datetime.now(mmt)` 
  - `app.py:534, 581, 597` — `datetime.now(timezone.utc)` for cache staleness
  - `app.py:3585` — bare `datetime.now()` without timezone — will be system local
  - `app.py:4090, 4124` — `datetime.now()` compared with DB dates
- **Fix:** Standardize on one timezone (recommend UTC for all internal operations, convert to MMT only for display). Store all dates in MySQL as UTC.

---

## 🟠 CODE QUALITY ISSUES

### 15. Monolithic 5343-Line app.py
- **Severity:** 🟠 HIGH
- **File:** `/root/psvibe_api_server/app.py` — 5,343 lines
- **Finding:** Single file contains 160+ functions including API routes, business logic, DB helpers, notification helpers, and utility functions. Hard to navigate, test, and maintain.
- **Fix:** Split into route modules by domain: `routes/members.py`, `routes/bookings.py`, `routes/inventory.py`, `routes/sessions.py`, etc.

### 16. Monolithic 6585-Line dashboard_routes.py
- **Severity:** 🟠 HIGH
- **File:** `/root/psvibe_api_server/dashboard_routes.py` — 6,585 lines
- **Finding:** Even larger than app.py. Contains 139 route handlers in a single file.
- **Fix:** Split into feature-specific route modules: `routes/dashboard_reports.py`, `routes/dashboard_finance.py`, etc.

### 17. Monolithic 2791-Line Sales Bot __init__.py
- **Severity:** 🟠 HIGH
- **File:** `/root/psvibe-sales-bot/bot/__init__.py` — 2,791 lines
- **Finding:** The main bot entry point is a single massive file. While handlers are modularized, the core bot logic is still monolithic.
- **Fix:** Extract conversation handlers, middleware, and utility functions into separate modules.

### 18. Functions Exceeding 100 Lines (15+ functions in app.py alone)
- **Severity:** 🟡 MEDIUM
- **Files:** Multiple
- **Findings (longest functions):**
  - `api_bookings_create()` — 194 lines (app.py:2961)
  - `api_sessions_start()` — 183 lines (app.py:2553)
  - `api_coupons_redeem()` — 168 lines (app.py:4107)
  - `api_update_booking_status()` — 152 lines (app.py:1635)
  - `api_start_console_session()` — 144 lines (app.py:2216)
  - `api_bot_booking_success_rate()` — 128 lines (app.py:3704)
  - `api_get_bookings()` — 125 lines (app.py:1859)
  - `api_bot_users_track()` — 120 lines (app.py:3494)
  - `api_sessions_move()` — 115 lines (app.py:2736)
  - `api_sessions_swap()` — 110 lines (app.py:2851)
- **Fix:** Break long functions into smaller helpers. Extract reusable validation, notification, and DB logic.

### 19. Missing Type Hints — 155/163 Functions
- **Severity:** 🟡 MEDIUM
- **File:** `/root/psvibe_api_server/app.py`
- **Finding:** Only 8 out of 163 functions have return type annotations. Similarly, dashboard_routes.py has only 1 function with return type out of 139.
- **Fix:** Add type hints gradually. Start with public API functions. Use `mypy` in CI.

### 20. Circular Import Pattern (patch_routes.py)
- **Severity:** 🟡 MEDIUM
- **Files:** `/root/psvibe_api_server/patch_routes.py:1, dashboard_routes.py:373, session_timer.py:88,92`
- **Finding:** `patch_routes.py` does `from app import *` at top level (excluding protected names), then uses lazy imports inside functions to avoid circularity. This is fragile and makes static analysis impossible.
  - `session_timer.py:88-92` — imports `_mysql_exec` and `_mysql_query` from app inside a function
  - `dashboard_routes.py:373` — imports `_sync_console_status` from app inside a function
- **Fix:** Extract shared DB helpers into a dedicated module (e.g., `db_client.py` which already exists) and import from there. No module should import from app.py internally.

### 21. Duplicate String `str,` at dashboards definition
- **Severity:** 🟢 LOW
- **File:** `/root/psvibe_api_server/app.py` (near endpoint definitions)
- **Finding:** A duplicate literal `str,` appears in the scraped data (line 384 match) suggesting a copy-paste artifact or syntax issue.
- **Fix:** Review and remove duplicate/artifact code.

### 22. Inconsistent Naming
- **Severity:** 🟢 LOW
- **Files:** Across all Python files
- **Finding:** Mixing of conventions: `_mysql_query` (private-ish prefix) vs `mysql_query` (public), `api_fetch_members` (api_ prefix) vs `webhook_booking_reminder` (webhook_ prefix), some camelCase in dict keys alongside snake_case.
- **Fix:** Adopt and enforce a naming convention. Use `routes/` prefix for route modules.

### 23. Dead/Commented Code — Auto-Cancel Background Thread
- **Severity:** 🟢 LOW
- **File:** `/root/psvibe_api_server/app.py:5338-5339`
- **Finding:** Lines 5338-5339 are commented out: `_bg_thread = threading.Thread(...)` / `_bg_thread.start()` — the auto-cancel-expired-pending feature appears to be disabled.
- **Fix:** Either remove dead code or document why it's commented out (e.g., "disabled — handled by cron instead").

### 24. TODO Items Across Codebase
- **Severity:** 🟢 LOW
- **Files:** 
  - `session_timer.py:174` — TODO enable inline buttons
  - `stock.py:190` — TODO Migrate to MySQL via API
  - `reports.py:244` — TODO Migrate to MySQL via API
  - `broadcast.py:107` — TODO Migrate to MySQL via API
- **Finding:** Several Google Sheets dependency references marked as TODO but still using the old pattern.
- **Fix:** Complete the migration or track these as tickets.

---

## 🟡 ARCHITECTURE & DESIGN

### 25. API Server and Sales Bot Share Notification Logic
- **Severity:** 🟡 MEDIUM
- **Finding:** Notification sending (`_send_telegram_customer`, `_notify_booking_received`, etc.) is duplicated between the API server (app.py) and the Sales Bot. The API server sends Telegram messages to customers directly using urllib instead of using the bot's client. This means two different notification paths exist.
- **Fix:** Either (a) route all notifications through a single service, or (b) extract notification logic into a shared module.

### 26. Reminder Logic Split Across Services
- **Severity:** 🟡 MEDIUM
- **Finding:** Booking reminders are handled in three places:
  1. `booking_reminder.py` — API server 30-min advance reminder
  2. `session_timer.py` — API server 5-min-before-end reminder
  3. Sales Bot — bot-side reminder management
  These can conflict or duplicate.
- **Fix:** Consolidate all reminder logic into a single service. Consider using a task queue (Celery, Redis Queue) instead of threading.Thread with sleep.

### 27. API Server + Sales Bot Both Query MySQL Directly
- **Severity:** 🟡 MEDIUM
- **Finding:** Both the API server and the Sales Bot connect directly to MySQL. The Sales Bot should ideally go through the API server for data access to maintain a single source of truth and consistent business logic.
- **Current state:** The Sales Bot has an `api_client.py` but many handlers also call direct Sheet/DB functions.
- **Fix:** Route all Sales Bot DB access through the API server's endpoints. Remove direct DB access from the bot.

### 28. Discord Bot Uses JSON Files as Database
- **Severity:** 🟡 MEDIUM
- **Files:** `/root/psvibe-discord-bot/` — `xp.json`, `warnings.json`, `suggestions.json`, `giveaways.json`, `achievements.json`, `tournaments.json`, `birthdays.json`, `lfg.json`, `tickets.json`, `events.json`
- **Finding:** The Discord bot uses 9+ flat JSON files as its primary data store. This creates risk of data corruption on concurrent writes, no ACID guarantees, no backup integration, and poor query performance.
- **Fix:** Move to MySQL (already available) for persistent data. At minimum, use SQLite for better reliability.

### 29. No Service Layer / Business Logic Separation
- **Severity:** 🟡 MEDIUM
- **Finding:** Business logic (validation, calculations, pricing) is mixed directly into route handlers in app.py and dashboard_routes.py. There's no service layer between the routes and the database.
- **Fix:** Create service modules for core domains (BookingService, MemberService, InventoryService) that encapsulate business rules.

### 30. Web Dashboard Has No Dedicated Backend
- **Severity:** 🟡 MEDIUM
- **Finding:** The Vue.js dashboard is served by FastAPI as static files and uses auth/login endpoints in the API server. But all data endpoints are mixed into `dashboard_routes.py` (6,585 lines) rather than being a separate service.
- **Fix:** Consider separating dashboard routes into a dedicated FastAPI router with clear `/dashboard/api/` prefix.

### 31. GSheet Legacy Code Still Present
- **Severity:** 🟡 MEDIUM
- **Finding:** Despite MySQL migration being largely complete, GSheet code remains in `sheets_client.py`, `config.py` (sheet names), and scattered throughout app.py with GSheet fallback logic (lines 537, 584, 600) for when MySQL data is "stale."
- **Fix:** Remove GSheet fallback once MySQL is fully trusted. Clean up dead GSheet config.

### 32. Zero Tests for API Server
- **Severity:** 🟠 HIGH
- **Finding:** `/root/psvibe_api_server/` has only one test file (`test_branch_filter.py` — 25 lines). No API endpoint tests, no unit tests for business logic, no integration tests. A 5,343-line app with zero test coverage is extremely risky.
- **Fix:** Add pytest for core business logic first, then API endpoint tests with TestClient. Use test fixtures with a test MySQL database.

### 33. Sales Bot Has Tests (6 test files) — But Not Comprehensive
- **Severity:** 🟢 LOW
- **Finding:** 6 test files exist in `/root/psvibe-sales-bot/tests/` covering games, main menu, console mgmt, members, reports, stock, sales, booking. Good start but likely not covering edge cases.
- **Fix:** Expand test coverage. Add API integration tests.

---

## 🟢 SECURITY

### 34. Debug Endpoint Exposes API Key Status
- **Severity:** 🟠 HIGH
- **File:** `/root/psvibe_api_server/app.py:320-335`
- **Finding:** `/api/debug_auth` endpoint returns info about API key matching, including whether the env key exists, whether query matches, etc. This is an information disclosure risk.
- **Fix:** Remove or restrict this endpoint to non-production environments.

### 35. API Key Passed via Query String
- **Severity:** 🟡 MEDIUM
- **Files:** `/root/psvibe_api_server/app.py:340-361`, Discord Bot API calls
- **Finding:** API authentication uses query parameter `?api_key=...` which gets logged in access logs, browser history, and proxy logs. JWT Bearer tokens are supported but the query param method is the primary.
- **Fix:** Transition to header-based authentication (X-API-Key or Authorization: Bearer) exclusively.

### 36. No Rate Limiting on Most Endpoints
- **Severity:** 🟡 MEDIUM
- **Finding:** Only a handful of endpoints use `_rate_limit`. Most API endpoints are unprotected against brute force or abuse. The webhook endpoints and receipt endpoint are completely open.
- **Fix:** Add rate limiting middleware (e.g., slowapi with FastAPI) for all endpoints, especially for auth, member lookup, and booking creation.

### 37. Path Traversal Risk in Receipt Endpoint
- **Severity:** 🟡 MEDIUM
- **File:** `/root/psvibe_api_server/app.py:3400-3402`
- **Finding:** `safe_id = voucher_id.replace("/", "-").replace("\\", "-")` — only filters `/` and `\` but not `..`. An attacker could potentially use `../` to traverse out of the receipt directory: `../../etc/passwd`.
- **Fix:** Use `os.path.basename()` or validate the cleaned path stays within the intended directory.

### 38. Token Exposure in Logs
- **Severity:** 🟡 MEDIUM
- **File:** `/root/psvibe_api_server/app.py:37`
- **Finding:** `_log.info("[NOTIFY] chat_id=%s token_len=%s", chat_id, len(token) if token else 0)` — logs the token length which is fine, but other places may log the full URL with token. Check `app.py:42` — bot token is embedded in the URL sent to Telegram API but not logged directly.
- **Fix:** Review all logging to ensure tokens are never logged. Use a logging filter that redacts `bot` + token patterns.

### 39. No CORS Origin Restriction
- **Severity:** 🟢 LOW
- **File:** `/root/psvibe_api_server/app.py` (CORS middleware config — not visible in this scan but implied by imports)
- **Finding:** CORS middleware is imported. Should verify it's restrictive.
- **Fix:** Confirm CORS allows only the dashboard origin.

---

## 🔵 PERFORMANCE

### 40. No DB Connection Pool Configuration
- **Severity:** 🟡 MEDIUM
- **File:** `/root/psvibe_api_server/mysql_db.py`
- **Finding:** MySQL uses a single global connection (`_pool`) with no connection pooling. Under concurrent load, this becomes a bottleneck.
- **Fix:** Use `DBUtils.PooledDB` or `SQLAlchemy` connection pooling instead of a single connection.

### 41. GSheet Cache Expiry Check on Every Request
- **Severity:** 🟢 LOW
- **File:** `/root/psvibe_api_server/app.py:534, 581, 597`
- **Finding:** Staleness check compares `last_updated` age for every request, falling back to GSheet if MySQL data is > stale threshold. This adds unnecessary overhead now that MySQL is primary.
- **Fix:** Remove GSheet fallback. Trust MySQL as single source of truth.

### 42. No Pagination on fetch_members
- **Severity:** 🟡 MEDIUM
- **File:** `/root/psvibe_api_server/app.py:784-800`
- **Finding:** `/api/fetch_members` returns ALL members without pagination. As membership grows, this will become a performance and memory issue.
- **Fix:** Add `limit`/`offset` query params and paginate results.

### 43. Thread.per-Reminder Instead of Scheduler
- **Severity:** 🟡 MEDIUM
- **Files:** `/root/psvibe_api_server/booking_reminder.py:117,247`
- **Finding:** Each booking reminder spawns a `threading.Thread` that `time.sleep()`s for the delay period. With many concurrent bookings, this creates many idle threads consuming resources.
- **Fix:** Use a proper scheduler like `APScheduler` or a priority queue with a single worker thread.

### 44. Missing Indexes — No Evidence of Index Analysis
- **Severity:** 🟡 MEDIUM
- **Finding:** No database migration files, no schema definitions with indexes visible. Common query patterns like `WHERE member_id = ?`, `WHERE console_id = ?`, `WHERE status = ? AND start_time < ?` may lack proper indexes.
- **Fix:** Audit MySQL slow query log. Add indexes on: `member_wallets(member_id)`, `console_booking(status, start_time)`, `stock_hold(booking_id)`, `customer_bot_users(tg_id)`, `topup_log(member_id, topup_date)`.

---

## ⚪ DOCUMENTATION & MAINTAINABILITY

### 45. No README or Documentation in API Server
- **Severity:** 🟡 MEDIUM
- **Finding:** The API server has no README.md, no architecture docs, no setup instructions. Understanding the codebase requires reading 5,343 lines of app.py.
- **Fix:** Add README.md with: architecture overview, setup instructions, API documentation links, environment variables reference.

### 46. No DB Schema Documentation
- **Severity:** 🟡 MEDIUM
- **Finding:** No schema.sql, no ERD diagram, no migration files. The database schema can only be inferred from SQL queries in the code.
- **Fix:** Create `schema.sql` with CREATE TABLE statements and comments. Generate ERD diagram.

### 47. Magic Numbers Throughout Codebase
- **Severity:** 🟢 LOW
- **Files:** Multiple
- **Findings:**
  - `INTERVAL 30 MINUTE` — used 6+ times for booking overlap windows
  - `INTERVAL 2 HOUR` — cancellation window
  - `timeout=5` — hardcoded URL request timeouts
  - `999` — magic fallback for missing last_seen date
  - `MINUTES` offset for MMT timezone (+6:30 hardcoded)
- **Fix:** Define named constants: `BOOKING_OVERLAP_WINDOW_MINS = 30`, `CANCELLATION_WINDOW_HOURS = 2`, `API_TIMEOUT_SECS = 5`, etc.

### 48. No Changelog / Version Tracking
- **Severity:** 🟢 LOW
- **Finding:** No CHANGELOG.md or version tags. Code comments mention dates like "Jun 25" but there's no systematic tracking.
- **Fix:** Start a CHANGELOG.md. Tag releases with semver.

### 49. Patch Files Indicate Technical Debt
- **Severity:** 🟡 MEDIUM
- **Files:** `patch_routes.py`, `patch_app.py`, `patch-app.py`, `fix_mysql_stock.py`, `fix_sheets_config.py`, `phase5_migrate.py`, `verify_patch.py`
- **Finding:** Multiple "patch" and "fix" files indicate ad-hoc fixes that weren't properly integrated into the main codebase. This is a sign of accumulated technical debt.
- **Fix:** Clean up patch files. Either integrate into main modules or document why they must remain separate.

### 50. Dashboard Files Cluttered at Root of Home Directory
- **Severity:** 🟢 LOW
- **Finding:** PS VIBE projects are spread across `/root/psvibe_api_server/`, `/root/psvibe-sales-bot/`, `/root/psvibe-dashboard/`, `/root/psvibe-discord-bot/` — not following the `/opt/kora-projects/` convention that other projects use.
- **Fix:** Consider migrating to `/opt/kora-projects/psvibe/` following the established convention.

---

## 📊 SUMMARY TABLE

| Category | Critical (🔴) | High (🟠) | Medium (🟡) | Low (🟢) | Total |
|----------|:---:|:---:|:---:|:---:|:---:|
| **Bugs & Logic Errors** | 4 | 6 | 4 | 0 | **14** |
| **Code Quality** | 0 | 3 | 3 | 3 | **9** |
| **Architecture & Design** | 0 | 1 | 7 | 1 | **9** |
| **Security** | 0 | 1 | 4 | 1 | **6** |
| **Performance** | 0 | 0 | 5 | 1 | **6** |
| **Documentation** | 0 | 0 | 4 | 2 | **6** |
| **TOTAL** | **4** | **11** | **27** | **8** | **50** |

---

## 🎯 PRIORITY ACTION ITEMS

### IMMEDIATE (This Week)
1. 🔴 **Rotate Discord bot token** — remove from source code
2. 🔴 **Rotate API key** — remove from Discord bot source
3. 🔴 **Move MySQL password to env var** — remove from mysql_db.py
4. 🔴 **Set MySQL root password** — never use empty password
5. 🔴 **Replace all bare `except:` blocks**
6. 🟠 **Add auth to webhook endpoints**
7. 🟠 **Remove debug endpoint from production**

### SHORT-TERM (This Month)
8. 🟠 **Remove default admin auto-creation** or generate random password
9. 🟠 **Fix N+1 queries** (member liability, leaderboard)
10. 🟠 **Wrap critical DB operations in transactions**
11. 🟡 **Standardize timezone handling** (all UTC)
12. 🟡 **Add pagination to list endpoints**
13. 🟡 **Add DB indexes for common query patterns**

### MEDIUM-TERM (Next Quarter)
14. 🟠 **Split app.py into route modules**
15. 🟠 **Add test coverage (pytest + TestClient)**
16. 🟡 **Consolidate reminder/notification systems**
17. 🟡 **Migrate Discord bot from JSON to MySQL**
18. 🟡 **Add proper connection pooling**

### LONG-TERM
19. 🟡 **Implement service layer pattern**
20. 🟡 **Remove GSheet legacy code**
21. 🟡 **Clean up patch files**
22. 🟢 **Add type hints, documentation, CHANGELOG**

---

*Report generated 2026-07-01 by Kora Subagent. No files modified during scan.*
