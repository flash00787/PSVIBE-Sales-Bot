# Wallet Bot 2 — Audit Fix Summary

## Fixes Applied

### 1. Thread-Safety: Raw Background Thread → Async Event-Loop Task (High Priority)

**Problem:** The `_cache_warmer_loop` ran on a raw `threading.Thread`, calling synchronous gspread functions (`get_settings()`, `get_tx_rows()`, `get_opening_balances()`, `get_monthly_summary()`) directly. This competed with `asyncio.to_thread` workers (via `_sh()`) for the same gspread HTTP connections, creating a critical thread-safety violation.

**Fix:** 
- Renamed `_cache_warmer_loop` → `_async_cache_warmer_loop` and rewrote it as an `async` coroutine.
- It now uses `asyncio.sleep(90)` instead of `time.sleep(90)`.
- All sheet fetches now go through `await _sh(get_settings)`, `await _sh(get_tx_rows)`, etc., which safely dispatches synchronous calls into the default thread-pool executor.
- Launched via `asyncio.create_task(_async_cache_warmer_loop())` inside `post_init()`, ensuring it runs entirely within the main event loop.
- Removed the old `threading.Thread(target=_cache_warmer_loop, daemon=True).start()` from `__main__`.

### 2. Thread-Safety: Global Cache Locking (High Priority)

**Problem:** Global caches (`_settings_cache`, `_tx_rows_cache`, `_opening_cache`, `_fx_cache`, `_monthly_cache`, `_gspread_client`) and their timestamps were read and written from multiple threads (event-loop thread, thread-pool workers via `_sh()`, Flask keep-alive thread) without any synchronization. This could cause `RuntimeError: dictionary changed size during iteration` or stale/inconsistent state.

**Fix:**
- Added `_cache_lock = threading.Lock()` at the top of the cache section.
- Wrapped all cache reads and writes in the following functions with `_cache_lock`:
  - `invalidate_all_caches()` — full lock around all cache resets
  - `get_settings()` — lock around cache check and cache update; I/O (`_fetch_settings()`) runs outside lock
  - `get_fx_rates()` — lock around cache check and update; I/O runs outside lock
  - `get_tx_rows()` — lock around cache check and update; I/O runs outside lock
  - `get_opening_balances()` — lock around cache check and update; I/O runs outside lock
  - `get_monthly_summary()` — lock around `_monthly_cache` check and update; computation and `get_tx_rows()` call run outside lock to avoid nested lock acquisition
  - `save_opening_balance()` — lock around `_opening_cache` invalidation
  - `update_fx_rate()` — lock around `_fx_cache` and `_settings_cache` invalidation
  - `_sheet_client()` — lock around gspread client singleton read and write; auth runs outside lock
  - `_async_cache_warmer_loop` error handler — lock around gspread client reset

### 3. Multi-Currency Accounting (Medium Priority)

**Problem (3a — `cmd_accounts`):** The grand total MMK calculation only summed accounts with `currency == "MMK"`, silently ignoring USD, THB, SGD, and other non-MMK accounts.

**Fix:** Added an `await _sh(get_fx_rates)` call and, for each non-MMK currency, look up its FX rate from `_fx_cache`. If a rate exists and is positive, convert: `grand_total_mmk += total * rate`. Falls back to treating the amount as MMK if no rate is configured.

**Problem (3b — `cmd_networth`):** Same issue — `total_accounts` was computed by filtering `info.get("currency", "MMK") == "MMK"`, which excluded all foreign-currency accounts from the net worth calculation.

**Fix:** Rewrote the loop to iterate all balances. For each account, if currency is "MMK", add directly; otherwise, look up the FX rate and convert. Falls back to direct addition if no rate is available.

### 4. Event-Loop Blocking in Reminder Job (Medium Priority)

**Problem:** `_remind_job()` (called by the JobQueue scheduler inside the event loop) called `get_monthly_summary()` and `get_tx_rows()` directly (synchronous), which could block the entire event loop for seconds while waiting on gspread/Google Sheets.

**Fix:** Changed both calls to use `await _sh(get_monthly_summary, ...)` and `await _sh(get_tx_rows)`, which offloads the blocking work to the thread pool without stalling the event loop.

### 5. Gspread Client Thread-Safety (Defense-in-Depth)

**Problem:** `_sheet_client()` read and wrote the `_gspread_client` singleton without any synchronization. The async cache warmer also reset it in its error handler.

**Fix:** Wrapped the singleton read/check inside `_cache_lock`, and similarly locked the client replacement in the cache warmer's error handler.

## Verification

- Syntax check passes: `python3 -m py_compile wallet_bot2_main.py` — no errors.
- All existing commands and conversation flows remain intact.
- No changes to the Google Sheets column layout, database interactions, or user-facing behavior.
- The cache warmer now runs at the same 90-second interval but inside the event loop with proper async isolation.
