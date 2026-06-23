# 🧠 Kora's Long-Term Memory

## People

- **Boss:** Ko Aung Chan Myint (ကိုအောင်ချမ်းမြင့်) — Founder of PS VIBE - PS5 Gaming Lounge. Call him "Boss" or "အစ်ကို" internally.
- **Osmo:** Discord username `@kingkong00787` — helped set up PS VIBE Discord server.

## Business: PS VIBE - PS5 Gaming Lounge

### Info
- **Tagline:** "Play The Game. Share The VIBE!"
- **Hours:** 9:00 AM - 9:00 PM daily
- **Address:** Yangon, Myanmar
- **Opened:** June 6, 2026 (Saturday) 🎮
- **Socials:** [Facebook](https://www.facebook.com/ps5gamecenter) | [TikTok](https://www.tiktok.com/@ps.vibe.game.cent)
- **Discord:** Guild ID 1516119712411422942 | [Invite](https://discord.gg/EXEF7phbZF)

### Infrastructure (bot-server-01: 5.223.81.16)
| Service | Purpose |
|---------|---------|
| psvibe-api | Main API server (port 8000) |
| psvibe-sale-bot | Staff sale/booking bot |
| psvibe_customer_bot | Customer-facing bot |
| psvibe-dashboard | Vue web dashboard (:9090) |
| kora-dashboard | Kora admin dashboard (:9091) |
| psvibe-discord-bot | Discord bot (35 commands) |
| MySQL | Primary database |
| cloudflared-tunnel | Cloudflare Tunnel |
| Caddy | Reverse proxy |
| n8n | Workflow automation |

### Key Operations
- **Member balance:** Column H of Card_wallet Google Sheet (legacy) → MySQL `member_wallets` (primary)
- **Receipts:** Burmese footer text must be removed
- **Coupon codes:** Valid samples: CBQVUHYG, CBANN6LD, CBZVNW7O, CBB292MP, CB7U617B

## 🧠 Critical Lessons Learned (Cumulative)

### Python Patterns
1. **`bool(0) == False`** — `"x if x else default"` breaks on 0. Use `"x if x is not None else default"`.
2. **`async def` + missing `await`** — coroutine objects silently pass type checks. Always use proper type hints.
3. **Unicode escape sequences in fix scripts** — `content.replace()` with escaped Unicode may not match file bytes. Use SFTP upload + remote execution instead.
4. **Systemd restart can silently fail** — verify PID; fallback to `kill -9` if needed.
5. **Elif chains must cover ALL variants** — `"wave"` ≠ `"wavepay"`.

### API & Database Patterns
6. **FastAPI response_model silently strips undeclared fields** — always audit response models against actual return shapes.
7. **Date format inconsistency** — Bot sends locale-dependent format (M/D/YYYY) but API expects YYYY-MM-DD. Always normalize at API boundary.
8. **API field naming is inconsistent** — camelCase (`customerName`, `timeSlot`) mixed with snake_case (`member_id`, `console_id`) in same response. Always verify field names exist before `.get()`.
9. **`today_str()` format ≠ API format** — `M/D/YYYY` vs `YYYY-MM-DD` — don't mix in comparisons.
10. **Double fail masking** — When both MySQL and GSheet fallback break simultaneously, root cause is masked. Monitor both paths independently.
11. **`%%` pattern doesn't work with `mysql.connector`** — uses `%s` parameter style, not printf. Pass format string as parameter.
12. **BotState IntEnum value collisions** — IntEnum auto-assigns values; collisions silently break ConversationHandler routing. Always verify uniqueness after edits. 10+ collisions found and fixed Jun 22.
13. **API response shape varies by endpoint** — `/api/bookings` returns time-only strings, `/api/dashboard/bookings` returns raw datetimes. Always check endpoint output before consuming.

### System Patterns
14. **NEVER touch ssh.socket.d** — A drop-in file created on June 11 crashed ssh.socket, taking ALL SSH down. VPS unrecoverable without Hetzner Console. Boss emphasized: "သေသေချာချာ တင်းတင်းကျပ်ကျပ် မှတ်ထားပါ".
15. **Gateway DNS failures** — Docker containers need explicit DNS config (Hetzner + Cloudflare) and `host` networking for reliable DNS.
16. **JS inline `<script>` blocks are fragile** — one syntax error kills ALL JavaScript in that block.
17. **Dashboard file deployment** — Base64 chunked SSH transfer reliable for large files. Kill stale processes before restart.
18. **`GROUP BY` collapses pipe-delimited data** — iterate all rows instead.
19. **DB stores ALL times in MMT (UTC+6:30)** — never assume UTC. `now_mmt()` is used throughout API. Timers, bookings, session times all MMT.
20. **`position: sticky` breaks with parent `overflow: hidden`** — frozen columns need parent without overflow clipping. Semi-transparent backgrounds also break visual freeze effect.

### Business Logic
21. **Same-console double booking** — Always check existing bookings at API level before allowing new ones.
22. **PNL depreciation must filter by purchase_date** — New assets don't accrue depreciation until month after purchase. Per agreed convention.
23. **Dashboard code is the source of truth** — Other API stubs may be outdated. Always check `dashboard_routes.py` first.
24. **FIFO for wallet consumption** — Oldest topups consumed first; bonus/free minutes have 0 Ks value.
25. **No Timer (duration=0) display** — Shows "∞ Open End" on Timeline. Conflict check uses 480 min (8hr) window. Never apply `duration or 60` pattern for display.

## Major Projects & Milestones

### Grand Opening (June 6, 2026)
- Data reset: All tables cleared except 4 confirmed bookings
- 10+ critical bugs fixed in 2 days leading up (coupon, wallet, booking, sales)
- All services active and stable

### Food Cart Feature (June 14)
- Phase 1 deployed: Staff can add food to active sessions via Console → Food Sale
- Food items auto-loaded into sale voucher at session end
- Phase 2 pending: Customer Bot self-ordering

### Finance System (June 15)
- PNL & Balance Sheet endpoints fixed (were broken stubs)
- Auto-depreciation script deployed (monthly cron, 1st of month)
- Auto-amortization for prepaid rent (monthly cron)

### Discord Bot (June 15-16)
- 35 slash commands across gaming, account, community, staff modules
- Auto-mod, birthday cron, LFG system, suggestion system
- Full integration with web dashboard feedback tab

### Suggestion System (June 17)
- Full pipeline: Discord → API → Dashboard
- Staff approve/reject with embed updates

### Console Timer & Booking System Overhaul (June 22)
- Console Timers page: live elapsed/remaining with 30s refresh, timer adjust dropdown
- Timeline AM/PM format + frozen console column
- No Timer support: "∞ Open End" display, 8hr conflict window
- Re-book cancelled bookings with date/time/duration modal
- Booking soft-delete (no physical deletions, 30-day cleanup)
- Auto-cancel disabled; manual-only end policy
- Customer Feedback dashboard page with stats, 14-day trend, full table

## ⚠️ Known Issues (Persistent)

| Issue | Severity | Status |
|-------|----------|--------|
| Feedback: 76% walk-in sessions lack telegram_chat_id | Medium | Deferred (Boss: keep as-is) |
| Feedback Dashboard page added (Jun 22) | — | Done |
| n8n payment (€25.68) overdue | Medium | Pending boss action |
| GitHub Deploy failing (psvibe-api-server) | Low | Pre-existing |
| Food Note issue — Phase 2 pending | Low | Deferred |
| VPS reboot caused DNS issues June 20 | Low | Mitigated |
| `_remind_loop` timer never fires | Low | Known, not critical |
| 100+ games claim vs 41 in DB | Low | Needs verification |
| food-cart/release silent fail (stock_out) | — | ✅ Fixed Jun 23 |
| Move API start_time reset | — | ✅ Fixed Jun 23 |
| booking_id path game_amt=0 | — | ✅ Fixed Jun 23 |

## Working Preferences

- **Language:** Burmese primary, English for tech terms
- **Timezone:** Asia/Yangon (UTC+6:30) — always convert for Boss
- **Delegation:** Always delegate complex tasks to sub-agents. Never do manually what a helper can do.
- **Fix protocol:** `python3 /root/coordination/fix_protocol.py --start <file>` before any code fix
- **Post-fix documentation:** Run `auto_doc_updater.py` + update daily memory + MEMORY.md
- **Sub-agent timeout:** 300s default

## 🆕 June 23, 2026 — Major Bug Fixes & Features

### Critical Bug Fixes
1. **start-session checked_in gap:** Query only checked `status='confirmed'`, missing `checked_in` bookings. Fixed to `status IN ('confirmed','checked_in')` at 5 locations. Always audit status filter lists for completeness.
2. **Auto-Checkin overlap false positive:** Auto-checkin booking caught itself as conflict. Fix: skip self-check via `if bk:`/`else:` conditional.
3. **Feedback routed to admin group:** `chat_id.startsWith('-')` check added in `console.py` — skip notifications when target is a group, not individual user.
4. **No Timer (duration=0) comprehensive fix:**
   - Timeline bar: extended to NOW instead of 5% fixed width
   - Utilization: counts up to NOW for live stats
   - Timezone: removed `+ 6.5 * 3600000` — browser provides MMT natively
   - Conflict check: `_dur_end = 360 if duration_mins == 0 else duration_mins` at 5 locations
5. **Session Reminder System — 3-type complete fix:**
   - Type 1 (API timer gap): `schedule_session_timer` now called from 5 start-session paths; `_bot_has_persistent_reminder()` reads `session_reminders.json`
   - Type 2 (Telegram format): `parse_mode: "Markdown"` with HTML `<b>` tags → HTTP 400. Changed to `parse_mode: "HTML"` consistently.
   - Type 3 (event loop): `resume_active_timers()` at module load time had no event loop → moved to FastAPI `lifespan` handler.
6. **console_mgmt.py import failure:** Module-level `__getattr__` lazy loader failed at runtime. Added explicit `import asyncio` + `from bot import fetch_console_status`.
7. **Receipt template overhaul (v1→v3):** Thermal 80mm format, base64 logo (no static file mount), AYA Pay fix, Topup field fixes, WALLET BALANCE section.

### New Features
8. **Active Session Move API:** `POST /api/sessions/move` — transaction-safe console swap with FOR UPDATE row locking, timer reschedule, conflict check.
9. **End Session Confirm Step:** Inline keyboard confirm dialog prevents accidental session endings.

### New Critical Lessons
- **`parse_mode` must match tag type** — "Markdown" + `<b>` = HTTP 400 Bad Request. Match format to content.
- **Module-level lazy `__getattr__` is fragile** — explicit imports are more reliable at runtime.
- **Destructive actions need confirm steps** — End Session, Cancel, Delete all benefit from inline confirm dialogs.
- **Event loop timing matters** — code running at module import time has no event loop. Use `lifespan` handler for async startup tasks.
- **No Timer (0 min) special-casing** — never use `duration or 60` / fallback pattern for display or logic. Use explicit `if duration_mins == 0` check everywhere: display, conflict check, utilization.
- **Status filter completeness** — when querying bookings by status, always verify ALL possible valid states are included. Missing `checked_in` = sessions silently invisible.
- **Base64-embedded assets** — avoid static file mounts for single-file deployments. Embed logos/images as base64 in HTML templates.
- **`from module import *` does NOT export underscore-prefixed names** — `_mc`, `_MYSQL_CFG` etc. are hidden. Must use explicit `from app import _mc` or local import inside function. Silent NameError → try/except returns 200 OK → stock_out never happens. This is a **double-fail silent bug pattern.**
- **API 200 OK on error is misleading** — always check error response body, not just HTTP status. `error_response()` should use non-200 status codes.
- **Move API must preserve start_time** — use `_bk["start_time"]`, not `_now`. Resetting start_time breaks session duration calculation.
- **booking_id paths must still calculate game_amt** — `if booking_id: game_amt = 0` is wrong. Booking customers still need game_amt from play time.
