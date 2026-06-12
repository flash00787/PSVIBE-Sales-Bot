# 🐛 Error Patterns — PS VIBE System

> Quick-reference error patterns. Detailed logs at `memory/bug-patterns.md`, `memory/lessons.md`.

## ☁️ SSH / Network / WARP

| Error | Pattern | Fix |
|-------|---------|-----|
| `Connection timed out` on ALL ports & ping | Cloudflare WARP installed & connected | `warp-cli --accept-tos disconnect` + `systemctl disable warp-svc` |
| SSH connects but password fails then re-prompts | Wrong password or WARP interfering with auth | Verify WARP disconnected; retry with correct password |
| `530 Origin unregistered` via Cloudflare | Tunnel process restarted; edge config stale | Restart tunnel (`systemctl restart cloudflared-tunnel`); wait 5s for edge sync |
| `context deadline exceeded` in tunnel logs | Tunnel origin (localhost:8000) not responding in time | Verify origin service active, restart if needed |

## 🤖 Telegram Bot Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| Menu button opens FAQ instead of correct feature | `_match_faq()` runs BEFORE button routing with score ≥2 | Move `_match_faq()` AFTER button routing in `handle_menu_buttons()` |
| Incomplete game list in session start | `books_games()` has `games_list[:30]` limit | Remove or increase the slice limit |
| Session End Timer reminders not arriving | `send_message()` lacks `message_thread_id` for Forum/topics mode | Pass `message_thread_id` from booking context → `_remind_loop` → `send_message()` |
| Timer reminder edits original msg instead of sending new one | `_remind_loop` uses `editMessageText` after timer elapses | Ensure `_remind_loop` sends NEW messages with `sendMessage` |
| Booking customer shown wallet check at session-end | `launch_session_sale()` checks wallet for ALL non-guest members | Add `if booking_id:` guard to skip wallet check for booking customers |
| FAQ auto-reply gives wrong game info | static FAQ data outdated (e.g., "100+ games" vs actual 41) | Comment out FAQ block in `handlers.py` until data corrected |
| `Can't parse entities` | MarkdownV2 unescaped `-` in text | `_to_mdv2()` escape before sending |
| Menu button not responding | `ConversationHandler` ate the button | Add to `_bk_intercept_menu()` in ALL text states |
| Garbled Burmese text | Unicode escape sequences corrupted by auto-fix pipeline | Use direct Unicode strings, never `\uXXXX` |
| Service not responding despite `active` status | systemd restart silently failed (PID unchanged) | Verify PID changed; `kill -9` if same |

## 🐍 Python Runtime Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| `NameError: name 'X' is not defined` | After code edit + restart — `.pyc` cache stale | `find ... -name '__pycache__' -type d -exec rm -rf {} +` then restart |
| `KeyError` | API response field name mismatch (e.g., `coupon_code` vs `code`) | Check API response_model and actual response |
| `KeyError: 0` | asyncio task crash, no visible error in journal | Add `set_exception_handler()` in main app |
| `"not enough arguments for format string"` | PyMySQL + `LIKE '%/%'` → Python `%` interpreted as format spec | Use `CONCAT('%', '/', '%')` |
| `SyntaxError` in API (service stuck `activating`) | Missing trailing comma in dict/list | `ast.parse()` before deploying |

## 🔧 API / Backend Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| FastAPI response stripped fields | `response_model` silences undeclared fields | Audit response_model vs actual return shapes |
| API `_api_get()` response empty | Double-unwrap: code checks `resp.get("success")` but API already unwrapped | Use response directly, don't check `success` |
| Auth 401 on localhost | API_KEY mismatch or service didn't fully restart | Debug endpoint, verify env, `kill -9` restart |
| Sales daily voucher shows wrong payment amount | payment_method column has wrong KPay value (e.g., 7100 vs 27100) | `UPDATE sales_daily SET payment_method = 'KPay:XXXX' WHERE id = N` |

## 🗄️ Database / MySQL

| Error | Pattern | Fix |
|-------|---------|-----|
| Missing data after MySQL migration | Key name mismatch (e.g., `"wave"` vs `"wavepay"`) | Audit all query keys against actual DB values |
| Account names not found in `cash_movements` | Code uses keys (`kbz_bank`) but DB stores labels (`KBZ Bank`) | Maintain mapping dict |
| `GROUP BY` collapses pipe-delimited values | `GROUP BY payment_method` merged rows | Iterate ALL individual rows instead |
| Game names mismatch across tables | `games_library` and `console_games` use different spellings | Update both tables to match; use `LIKE` fallback for encoding issues |
| Dashboard shows wrong game status | `final_status` not using supported values (only: Available, Damaged, Lost, In Use) | Update to Dashboard-compatible values only |

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

## ⚠️ Lessons (Don't Repeat)

| Lesson | Context |
|--------|---------|
| WARP breaks direct SSH to VPS | Installed at 01:29 MMT Jun 12; all incoming traffic dropped |
| NEVER modify `disc_count` without explicit Boss approval | FC 26 disc_count=10 is intentional (physical disc copies) |
| Staff group has Forum/topics mode | All messages need `message_thread_id` or staff won't see them |
| Sales bot restart doesn't change PID on silent failure | Always verify with `systemctl status` after restart |
