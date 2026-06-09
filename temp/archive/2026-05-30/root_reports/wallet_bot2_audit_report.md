# Personal Wallet Bot 2 — Deep Software Engineering Audit Report

## Executive Summary
This report presents a comprehensive software engineering audit of the Personal Wallet Bot 2 (`wallet_bot2_main.py`). The application is a Telegram-based financial manager built using `python-telegram-bot` and integrated with Google Sheets via `gspread` for data storage, retrieval, and calculations.

While functional, the codebase exhibits critical architectural, performance, and robustness vulnerabilities that present major risks of service disruption, data corruption, and system crashes under production loads.

---

## Critical Security/Crash Bugs (Priority: High)

### 1. Asynchronous Event-Loop Blocking & Server Starvation
* **Finding:** The application relies on `gspread` (a synchronous HTTP-backed library) inside synchronous helper methods (e.g., `_sheet_client()`, `_get_sheet()`, `_fetch_settings()`, `_fetch_tx_rows()`, and `_fetch_opening_balances()`). These are executed via `asyncio.to_thread` via the wrapper `_sh(fn, *args)`. However, the background cache-warmer thread (`_cache_warmer_loop`) calls synchronous, non-thread-safe cache-population operations (`get_settings()`, `get_tx_rows()`, etc.) directly on a standard Python thread without synchronization.
* **Risk:** Simultaneously calling standard synchronous `gspread` HTTP requests across the background cache-warmer thread and multiple `asyncio` thread-pool workers creates a critical **thread safety violation**. The underlying `urllib3` connection pools or `requests.Session` instances inside `gspread` / `google-auth` can enter invalid states, causing corrupted memory, data corruption, or silent network stalls.
* **Fix:** Avoid background thread pooling of synchronous APIs without dedicated, isolated connection sessions. Transition the background cache warmer to run as an asynchronous task inside the main event loop using `asyncio.sleep()`, executing its fetches safely via `_sh()`.

### 2. Thread-Safety Violations in Global Caches
* **Finding:** Global caches (such as `_settings_cache`, `_tx_rows_cache`, `_opening_cache`, and `_fx_cache`) and their timestamps are modified and read without any thread-locking synchronization mechanisms.
* **Risk:** Python's Global Interpreter Lock (GIL) does not protect dictionary operations or complex cache-invalidation assignments from race conditions. When the background cache-warmer thread executes `invalidate_all_caches()` or writes to these dicts while an active `asyncio` worker thread pool is reading them, it will result in `RuntimeError: dictionary changed size during iteration` or unhandled state inconsistencies.
* **Fix:** Implement a threading lock (`threading.Lock`) or transit the cache warmer into the main asyncio event loop to ensure single-threaded sequential execution of state mutations.

### 3. File Descriptor Leak in Singleton Lock File
* **Finding:** At startup, the single-instance locking logic does the following:
  ```python
  lock_file = open(_lock_path, "w")
  try:
      fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
  except OSError:
      ...
  ```
* **Risk:** The lock file descriptor is never closed on successful acquisition. While this keeps the lock active, if the self-healing loop restarts `main()`, repeated invocations of initialization code can leak file descriptors over time if they aren't structured carefully within clean process lifecycles.
* **Fix:** Explicitly register an exit handler or cleanly structure the lock wrapper so it spans the entire process life safely.

---

## Logical/Functional Flaws (Priority: Medium)

### 1. Dynamic Row Index Drift during Concurrent Operations
* **Finding:** In `save_transaction()`, if a row number is not specified, it calculates the target row using:
  ```python
  col_b = ws.col_values(2)
  last_data_row = len(col_b) # logic parsing B
  ```
* **Risk:** This read-then-write approach is highly prone to **race conditions** if two transactions are logged simultaneously. Multiple async workers can read the exact same `col_values()`, determine identical row indices, and overwrite each other's data rows on Google Sheets.
* **Fix:** Use Google Sheets API's atomic `append_row` operations where possible, or employ sheet locks.

### 2. Multi-Currency Accounting Imbalances
* **Finding:** In `get_account_balances()`, accounts with non-MMK currencies are parsed based on substring matches of their names (e.g., matching "USD", "THB", etc.). However, when computing the final Grand Total MMK, only accounts with the exact currency matching "MMK" are factored in.
* **Risk:** Outstanding balances in foreign accounts are silently ignored during total calculations instead of dynamically converting them using FX rates.
* **Fix:** Map each account's current balance through the real-time `_fx_cache` to present an accurate unified grand total in MMK.

---

## Gspread / Google Sheets Quota/API Optimization Suggestions (Priority: Low)

### 1. Excessive Quota Consumption (Rate Limits)
* **Finding:** The background cache-warmer runs every 90 seconds, clearing all caches and fetching settings, transaction logs, opening balances, and monthly summaries sequentially. This can easily trigger the 300-reads-per-minute Google Sheets API rate limit (HTTP 429).
* **Fix:** Reduce the warming frequency to 5–10 minutes, and use batch reads (`spreadsheets.values.batchGet`) to fetch data from multiple tabs in a single HTTP call.

---

## Code Quality & Maintainability Improvements

1. **Explicit Error Handling:** Replace generic `except Exception:` blocks in parser functions with targeted exceptions (e.g., `ValueError`, `TypeError`).
2. **Configuration Management:** Cleanly encapsulate environment variable parsing to prevent potential runtime parsing crashes.
3. **Robust Date Parsing:** Upgrade raw structural indexes `row[1]` and `row[3]` into structured named dict or dataclass representations to avoid out-of-range IndexErrors.

---
*End of Report.*
