# 🔧 Customer Bot — Fix Plan

**Date:** 2026-05-28
**Based on:** Audit Report + VPS Ground-Truth Verification
**VPS:** 5.223.81.16 | **Repo:** /root/psvibe-sale-bot/customer_bot/
**API Server:** /root/psvibe_api_server/app.py (uvicorn :8000, pid 340787)

---

## 📊 Summary of Findings

| # | Severity | Issue | Effort |
|---|---|---|---|
| P0-1 | 🔴 CRITICAL | 12 API endpoint paths WRONG — every fetch returns 404 | ~1-2 hrs |
| P0-2 | 🔴 CRITICAL | `booking.py` MISSING — 3 command handlers crash on call | ~3-4 hrs |
| P0-3 | 🔴 CRITICAL | 16 booking states ALL stubbed (`lambda: None`) | ~3-4 hrs |
| P1 | 🟠 HIGH | 7 backend endpoints DON'T EXIST — need creating | ~4-6 hrs |
| P1 | 🟠 HIGH | Feedback callback pattern mismatch | ~30 min |
| P2 | 🟡 MEDIUM | Duplicate constants, dead code, missing keyboard | ~2 hrs |

---

## P0-1: API Path Mapping (Verified Against Live Server)

### Paths That Point to Existing Backend Endpoints

| # | Bot Function | Current (WRONG) Path | Correct Backend Path | Backend Returns |
|---|---|---|---|---|
| 1 | `_fetch_games_full` | `GET /api/sheets/game-library` | `GET /api/fetch_games` | `ok(all_games)` → `{"success":true,"data":[...]}` |
| 2 | `_fetch_members` | `GET /api/sheets/members-list` | `GET /api/fetch_members` | `ok(sorted(members))` → `{"success":true,"data":[...]}` |
| 3 | `_fetch_consoles` | `GET /api/sheets/consoles` | `GET /api/fetch_console_status` | `ok(consoles)` → `{"success":true,"data":[{...}]}` |
| 4 | `_fetch_promotions` | `GET /api/sheets/promotions` | `GET /api/fetch_promotions_cached` | `ok(promos)` → `{"success":true,"data":[...]}` |
| 5 | `_fetch_config` | `GET /api/sheets/config` | `GET /api/sheets/config` | ✅ **ALREADY CORRECT** |
| 6 | `_fetch_sales_data` | `GET /api/sheets/sales-summary` | `GET /api/analytics/daily_sales` | `ok(get_daily_sales(date))` |

### Paths Requiring NEW Backend Endpoints

| # | Bot Function | Path Called | Method | What Bot Expects |
|---|---|---|---|---|
| 7 | `_fetch_contacts` | `api/sheets/settings/contacts` | GET | `{contacts: [{username, label/name, role, phone}]}` |
| 8 | `_get_linked_phone` | `api/bookings?telegramChatId=X` | GET | List of bookings with `phone`, `status`, `createdAt` |
| 9 | `cmd_menu` (line 162) | `api/bookings?telegramChatId=X&date=Y&status=Z` | GET | Today's bookings for user |
| 10 | `cmd_today` (line 337) | `api/bookings?date=Y&status=Z` | GET | All today's confirmed bookings |
| 11 | `cmd_mybookings` (line 539) | `api/bookings?date=Y&status=Z` | GET | User's bookings on date |
| 12 | `_text_cancel_booking` (line 778) | `api/bookings/{id}` | GET | Single booking details |
| 13 | `_text_cancel_booking` (line 788) | `api/bookings/{id}/status` | PATCH | Update booking status |
| 14 | `log_to_sheet` | `api/sheets/log` | POST | Accept `{tg_id, username, user_name, query, response, sentiment}` |
| 15 | `track_usage` | `api/bot-users/track` | POST | Accept `{tg_id, username, user_name, action, member_id, phone}` |
| 16 | `cmd_feedback` (handlers.py:722) | `api/feedback` | POST | Accept `{tg_id, username, booking_id, rating, comment}` |

### ⚠️ ADDITIONAL ISSUE: Response Format Mismatch

The API server wraps ALL responses in:
```json
{"success": true, "data": <actual_data>}
```

But the customer bot accesses data directly:
```python
# api.py _fetch_games_full()
data = await _api_get("sheets/game-library")  # Returns {"success":true,"data":[...]}
games = (data or {}).get("games", [])          # ❌ "games" key doesn't exist at top level
```

**Fix needed:** Either (a) unwrap in each `_fetch_*` function using `data.get("data")`, or (b) unwrap in `_validate_response`.

Similarly for members:
```python
data = await _api_get("sheets/members-list")  # Returns {"success":true,"data":["M001","M002",...]}
members = {m["member_id"]: m for m in (data or {}).get("members", [])}  # ❌
# Fix: data = (data or {}).get("data", {})
# members = {m: {...}} for m in data  (it's a flat list of IDs!)
```

**The `api_fetch_members` returns a flat list of member ID strings**, not dicts with `member_id` keys. The customer bot treats them as dicts with member_id, name, phone, etc. This means even with the right path, the data structure is wrong. The customer bot needs `api_fetch_member_data/{member_id}` for detailed member info, or the members endpoint needs to be enhanced.

---

## P0-2: Missing booking.py

### Status: CONFIRMED MISSING
```
ls: /root/psvibe-sale-bot/customer_bot/booking.py → NOT FOUND
```

### Source Files Found (STAFF bot only — NOT compatible):
- `/root/psvibe-sale-bot/handlers/booking.py` (1073 lines) — Uses `from bot import *`, `_replit_get()`, sync patterns
- `/root/psvibe-sale-bot/bot/handlers/booking.py` (1077 lines) — Same pattern, `SBK_*` states

### Original Source: `_v1_compat.py` — DELETED
- Removed 2026-05-28 (today), per docstrings in `main.py` and `__init__.py`
- No git history available on VPS
- No `.bak` files found anywhere
- No Docker volume backups

### Functions Needed in booking.py

These are imported by `handlers.py` (lazy imports at lines 812-823):
| Function | Purpose |
|---|---|
| `cmd_mybookings(update, context)` | List user's bookings with cancel buttons |
| `cmd_refer(update, context)` | Show referral code and referral program info |
| `cmd_waitlist(update, context)` | Waitlist entry flow for fully-booked times |

### Approach: Recreate from Scratch

Since `_v1_compat.py` is gone and staff booking handlers are incompatible (different imports, state systems, and sync vs async), the most reliable approach is to recreate the three functions by reading what `handlers.py` expects and building against the API.

**Alternative:** The `bot/handlers/booking.py` has `cmd_staff_book_hub` and related booking logic. The `bot/handlers/waitlist.py` has waitlist management. These could be adapted, but require:
1. Replacing `from bot import *` with explicit imports
2. Converting `_replit_get()` calls to async `_api._api_get()`
3. Rewriting `ReplyKeyboardMarkup` to `InlineKeyboardMarkup` where appropriate
4. Mapping `SBK_*` state patterns to `BK_*` patterns

---

## P0-3: Booking Conversation Stubs

### 16 Stubbed States in main.py (lines 74-87)

```python
BK_MEMBER_CHECK:  [CallbackQueryHandler(lambda u,c: None, pattern=r"^bk_mem:")],
BK_MEMBER_SELECT: [CallbackQueryHandler(lambda u,c: None, pattern=r"^bk_sel:")],
BK_PHONE_VERIFY:  [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u,c: None)],
BK_DATA_CONFIRM:  [CallbackQueryHandler(lambda u,c: None, pattern=r"^bk_dc:")],
BK_NAME:          [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u,c: None)],
BK_PHONE:         [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u,c: None)],
BK_DATE:          [CallbackQueryHandler(lambda u,c: None, pattern=r"^bkdate:")],
BK_TIME:          [CallbackQueryHandler(lambda u,c: None, pattern=r"^(bktime:|bk_custom:)")],
BK_CONSOLE:       [CallbackQueryHandler(lambda u,c: None, pattern=r"^bk_con:")],
BK_DURATION:      [CallbackQueryHandler(lambda u,c: None, pattern=r"^bk_dur:")],
BK_GAME:          [CallbackQueryHandler(lambda u,c: None, pattern=r"^bk_game:")],
BK_CONSOLE_PREF:  [CallbackQueryHandler(lambda u,c: None, pattern=r"^bk_cp:")],
BK_CONFIRM:       [CallbackQueryHandler(lambda u,c: None, pattern=r"^bk_ok:")],
BK_END:           [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u,c: None)],
# BK_DUP_WARN, BK_DISC_WARN, BK_CON_CONFLICT are states defined but NOT in the ConversationHandler
```

### Required Booking Handler Functions

Each state needs a real async handler. The flow is:
1. **BK_MEMBER_CHECK** → Ask "Do you have a member card?" → Yes/No buttons (`bk_mem:yes`, `bk_mem:no`)
2. **BK_MEMBER_SELECT** (if yes) → Look up member by ID → show matches (`bk_sel:{id}`)
3. **BK_PHONE_VERIFY** → Verify phone matches member record → confirm (`bk_dc:ok`, `bk_dc:edit`)
4. **BK_DATA_CONFIRM** → Show retrieved data, proceed
5. **BK_NAME** (if new) → Enter name
6. **BK_PHONE** (if new) → Enter phone
7. **BK_DATE** → Pick date (`bkdate:today`, `bkdate:tomorrow`, `bkdate:custom`)
8. **BK_TIME** → Pick time slot (`bktime:10:00`, `bk_custom:14:30`)
9. **BK_CONSOLE** → Pick console (`bk_con:C-01`, etc.)
10. **BK_DURATION** → Pick duration (`bk_dur:1`, `bk_dur:2`, etc.)
11. **BK_GAME** → Enter game name
12. **BK_CONSOLE_PREF** → Enter console preference notes
13. **BK_CONFIRM** → Show summary → Confirm (`bk_ok:confirm`)
14. **BK_DUP_WARN** → Warn about duplicate booking
15. **BK_DISC_WARN** → Warn about discount conflict
16. **BK_CON_CONFLICT** → Warn about console conflict

### Key insight: `cmd_book` already exists!

```python
async def cmd_book(update, context):
    asyncio.create_task(_api.track_usage(update.effective_user, "book_start"))
    context.user_data["bk_reserved_console"] = None
    await update.message.reply_text(
        "📅 *Booking Form*\n\nပထမဆုံး — Member card ရှိတယ်ဆိုရင်...",
        parse_mode="Markdown",
    )
    return BK_MEMBER_CHECK
```

The entry point WORKS. Only the state handlers are stubbed. Each state handler needs to:
1. Parse the callback data or message text
2. Store the value in `context.user_data`
3. Return the next state

The real work is implementing 16 state handlers + helper functions to interact with the API.

---

## Backend Endpoints to Create (P1)

All endpoints require adding routes to `/root/psvibe_api_server/app.py`:

| # | Endpoint | Method | Priority | Input | Output |
|---|---|---|---|---|---|
| 1 | `/api/sheets/settings/contacts` | GET | 🔴 HIGH | — | `{contacts: [{username, label, name, role, phone}]}` |
| 2 | `/api/bookings` | GET | 🔴 HIGH | Query: `telegramChatId`, `date`, `status` | List of booking dicts with phone, status, createdAt |
| 3 | `/api/bookings/{booking_id}` | GET | 🔴 HIGH | Path: `booking_id` | Single booking dict |
| 4 | `/api/bookings/{booking_id}/status` | PATCH | 🟠 MED | Body: `{status: "cancelled"}` | Updated booking |
| 5 | `/api/feedback` | POST | 🟠 MED | Body: `{tg_id, username, booking_id, rating, comment}` | Confirmation |
| 6 | `/api/sheets/log` | POST | 🟡 LOW | Body: `{tg_id, username, user_name, query, response, sentiment}` | Confirmation |
| 7 | `/api/bot-users/track` | POST | 🟡 LOW | Body: `{tg_id, username, user_name, action, member_id, phone}` | Confirmation |

### Data Sources for New Endpoints

- **Contacts:** From `Setting` sheet — check columns for admin usernames/phones. The customer bot's `cmd_contact` also has a hardcoded fallback `@psvibeofficial` and `09 773355 915`.
- **Bookings:** From `Console_Booking` sheet — need a new column for `telegramChatId` (currently not tracked). The staff bot creates bookings via `api_create_booking` which writes to `Console_Booking` but doesn't include `telegramChatId`.
- **Feedback:** New destination needed — feedback sheet or append to existing sheet.
- **Logs/Usage:** New sheets or append to existing. The sales bot already tracks usage via gspread directly; adding API endpoints would unify access.

---

## P1: Feedback Callback Pattern Mismatch

### Current (Broken) Registration in main.py:

```python
# Pattern registered:  ^fb:comment_prompt:
# Button data used:    fbc:{rating}:{bk_id}
# Pattern registered:  ^fb:skip$
# Button data used:    fbskip
```

### Fix: Change patterns to match actual button callback_data:

| Handler | Current Pattern | Correct Pattern |
|---|---|---|
| `cb_feedback_comment_prompt` | `^fb:comment_prompt:` | `^fbc:` |
| `cb_feedback_skip` | `^fb:skip$` | `^fbskip$` |

---

## Files to Modify (Complete List)

### Phase 1 — API Path Fixes (customer_bot/api.py)

| Line | Change |
|---|---|
| 251 | `"sheets/game-library"` → `"fetch_games"` |
| 266 | `"sheets/members-list"` → `"fetch_members"` |
| 284 | `"bookings?telegramChatId="` → keep path, needs backend endpoint |
| 320 | `"sheets/consoles"` → `"fetch_console_status"` |
| 336 | `"sheets/settings/contacts"` → needs backend endpoint |
| 351 | `"sheets/promotions"` → `"fetch_promotions_cached"` |
| 381 | `"sheets/sales-summary"` → `"analytics/daily_sales"` |
| 468 | `"sheets/log"` → needs backend endpoint |
| 482 | `"bot-users/track"` → needs backend endpoint |

### Phase 1b — Response Format Unwrapping (customer_bot/api.py)

Each `_fetch_*` function that hits the API server must unwrap `{"success":true,"data":...}`:

```python
# Before (wrong):
data = await _api_get("sheets/game-library")
games = (data or {}).get("games", [])

# After (correct):
raw = await _api_get("fetch_games")
data = (raw or {}).get("data", [])  # unwrap FastAPI ok() wrapper
games = data  # fetch_games returns list directly, not {games: [...]}
```

### Phase 2 — Create customer_bot/booking.py

New file with:
- `cmd_mybookings(update, context)` — async
- `cmd_refer(update, context)` — async
- `cmd_waitlist(update, context)` — async

### Phase 3 — Replace Booking State Stubs (customer_bot/main.py)

Replace all 16 `lambda u,c: None` with real async handler functions imported from booking.py (or handlers.py).

### Phase 4 — Backend Endpoints (api_server/app.py)

Add routes for contacts, bookings query, booking detail, status update, feedback, log, and bot-users tracking.

---

## Execution Order

1. ✅ **Fix API paths** — Makes all existing features start working
2. ✅ **Add response unwrapping** — Fixes data access after correct paths return data
3. ✅ **Create booking.py** — Prevents import crashes on /mybookings, /refer, /waitlist
4. ✅ **Implement booking states** — Enables the full booking conversation flow
5. ✅ **Create backend endpoints** — Unblocks contacts, booking queries, feedback, logging
6. ✅ **Fix feedback callback patterns** — Makes rating/comment flow work
7. ✅ **Clean up P2 issues** — Remove duplicates, add keyboard, fix cancel double-registration

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| API response format differs per endpoint | HIGH | MEDIUM | Test each endpoint individually after path fix |
| `fetch_members` returns flat list, not dicts | HIGH | HIGH | Need to rewrite `_fetch_members()` to call `fetch_member_data/{id}` per member, OR enhance backend |
| Booking sheet lacks `telegramChatId` column | HIGH | HIGH | Must add column to `Console_Booking` sheet, update `create_booking` endpoint |
| No backup of `_v1_compat.py` | CONFIRMED | HIGH | Must rewrite booking handlers from scratch |
| API server restart needed for new endpoints | LOW | LOW | `systemctl restart psvibe_api_server` |
