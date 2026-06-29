# ERROR_PATTERNS.md — Common Bugs & Anti-Patterns

> Auto-generated from MEMORY.md Critical Lessons Learned.
> **Purpose:** Prevent repeating the same mistakes across projects.

## System Patterns

| # | Pattern | Lesson |
|---|---------|--------|
| 28 | Never edit minified Vue build output | Always edit source `.vue` files and rebuild. Single-character name conflicts break entire components. |
| 29 | Vite builds replace all hashes | Every rebuild generates new content hash filenames. Old files must be cleaned. |
| 30 | JS object key sorting trap | String keys that look like integers (e.g., "848") sorted numerically by V8. `.reverse()` on `Object.values()` doesn't reverse insertion. |
| 31 | Lane stacking is wrong UX for timeline overlaps | Use natural overlap + tap-to-select popup. Don't force lane splitting. |
| 32 | `window` object not available in Vue `<template>` | Use computed properties or method-returned style objects. |
| 33 | SQLite FOREIGN KEY enforcement | Must enable `PRAGMA foreign_keys = ON` per connection. |
| 34 | FastAPI query params vs path params | Path params auto-convert types; query params are strings. Validate manually. |
| 35 | CORS middleware ordering | Must be added BEFORE route registration in FastAPI. |
| 36 | FIFO matching complexity | Multi-currency FIFO with charges requires tracking remaining quantities per lot. Test partial sales. |
| 37 | JS Date(YYYY-MM-DDTHH:MM:SS) is LOCAL time | Without Z/timezone suffix, interpreted in browser timezone. Always append Z for UTC DB timestamps. |
| 38 | Server-side filter > client-side | MySQL NOW() - INTERVAL more reliable than browser JS Date parsing. |

## API & Database Patterns

| # | Pattern | Lesson |
|---|---------|--------|
| 44 | `unwrap_response()` changes response structure | Don't access `.data` again after unwrap. |
| 45 | `import X as Y` aliasing | `import urllib.request as _urllib` means `_urllib` IS the module. Call `_urllib.urlopen()`. |
| 46 | Never duplicate financial calculation logic | Two endpoints, two different results. Shared function = single source of truth. |
| 51 | docker exec mysql auth pitfalls | Container internal MySQL client connects as different host (`127.0.0.1`). Use pymysql from host. |
| 52 | CallbackQueryHandler ≠ MessageHandler | CallbackQueryHandler does NOT accept filters. Use in-handler checks. |
| 53 | GROUP BY raw strings is wrong | When column stores `Cash:20000`, creates separate groups per amount. Use `SUBSTRING_INDEX()`. |
| 54 | Two endpoints, same action = divergence | Always check ALL paths that perform the same action for missing side effects. |
| 55 | Check ALL tables after migration | Don't assume legacy table names still have data. Verify both old and new tables. |

## Business Logic

| # | Pattern | Lesson |
|---|---------|--------|
| 47 | Leave policy — any leave = forfeit attendance | Attendance bonus is binary (present → full, absent → 0), not prorated. Extra penalty only when >2 days. |
| 48 | Food profit = reuse PNL logic | Don't recalculate from sales_daily alone. PNL already has FIFO COGS. |
| 49 | Rename carefully — check all code paths | `food_charges`→`food_allowance`: must update SELECT, variables, labels, form fields. |
| 50 | Gmail OAuth tokens expire | refresh_token can be revoked. Use desktop redirect flow for re-auth. |

## Telegram Bot Patterns

| # | Pattern | Lesson |
|---|---------|--------|
| 26 | API format changes after migration | When API returns different format, check ALL consumers. |
| 27 | Minified JS edits | Use Python string replace for precision, not sed. Always backup first. |
| — | Markdown escape in bot messages | Every screen with `parse_mode="Markdown"` must escape `_`, `*`, `` ` ``, `[`. Apply at display time. |

## Fix Protocol (Always)

1. `python3 /root/coordination/fix_protocol.py --start <file>` before any code fix
2. `python3 /root/coordination/auto_doc_updater.py --summary "..."` after fix
3. Update daily memory + MEMORY.md
4. Clean temp files
