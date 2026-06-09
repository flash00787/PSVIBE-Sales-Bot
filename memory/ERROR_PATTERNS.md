# 🐛 Error Patterns — PS VIBE System

> Quick-reference error patterns. Detailed logs at `memory/bug-patterns.md`, `memory/lessons.md`.

## 🐍 Python Runtime Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| `NameError: name 'X' is not defined` | After code edit + restart — `.pyc` cache stale | `find ... -name '__pycache__' -type d -exec rm -rf {} +` then restart |
| `KeyError` | API response field name mismatch (e.g., `coupon_code` vs `code`) | Check API response_model and actual response |
| `KeyError: 0` | asyncio task crash, no visible error in journal | Add `set_exception_handler()` in main app |
| `"not enough arguments for format string"` | PyMySQL + `LIKE '%/%'` → Python `%` interpreted as format spec | Use `CONCAT('%', '/', '%')` |
| `SyntaxError` in API (`activating` forever) | Missing trailing comma in dict/list | `ast.parse()` before deploying |

## 🤖 Telegram Bot Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| `Can't parse entities` | MarkdownV2 unescaped `-` in text | `_to_mdv2()` escape before sending |
| Menu button not responding | `ConversationHandler` ate the button | Add to `_bk_intercept_menu()` in ALL text states |
| Garbled Burmese text | Unicode escape sequences corrupted by auto-fix pipeline | Use direct Unicode strings, never `\uXXXX` |
| Service not responding despite `active` status | systemd restart silently failed (PID unchanged) | Verify PID changed; `kill -9` if same |

## 🔧 API / Backend Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| FastAPI response stripped fields | `response_model` silences undeclared fields | Audit response_model vs actual return shapes |
| API `_api_get()` response empty | Double-unwrap: code checks `resp.get("success")` but API already unwrapped | Use response directly, don't check `success` |
| Auth 401 on localhost | API_KEY mismatch or service didn't fully restart | Debug endpoint, verify env, `kill -9` restart |

## 🗄️ Database / MySQL

| Error | Pattern | Fix |
|-------|---------|-----|
| Missing data after MySQL migration | Key name mismatch (e.g., `"wave"` vs `"wavepay"`) | Audit all query keys against actual DB values |
| Account names not found in `cash_movements` | Code uses keys (`kbz_bank`) but DB stores labels (`KBZ Bank`) | Maintain mapping dict |
| `GROUP BY` collapses pipe-delimited values | `GROUP BY payment_method` merged rows | Iterate ALL individual rows instead |

## 🚀 Sub-agent / Spawn Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| "Something went wrong" after spawn | Sub-agent finished with empty output (no text) | Every spawn MUST have SAFETY NET with completion marker |
| Session write lock timeout | `acquireTimeoutMs` default 60s too short | Increase to 300s; enable maintenance mode |
| "Invalid taskName" | Hyphens in task name | Use only `[a-z][a-z0-9_]*` |
| Parallel agent collision | 2+ agents modifying same function | Check lock manager first; sequential on shared files |

## 📋 Git / Deployment

| Error | Pattern | Fix |
|-------|---------|-----|
| `git push` blocked | SA JSON or token in commit history | NEVER commit secrets; `git filter-branch` if needed |
| Service shows `activating` (not `active`) | SyntaxError in Python file from auto-fix | Check journal, fix SyntaxError, restart |
