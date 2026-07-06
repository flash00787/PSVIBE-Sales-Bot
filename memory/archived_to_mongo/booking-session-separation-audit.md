# Booking vs Session — Separation Audit
> **Generated:** 2026-07-01 | **Author:** Kora Subagent  
> **Scope:** AUDIT ONLY — No code changes

---

## Executive Summary (Burmese)

Boss — `console_booking` table ထဲမှာ Booking (ကြိုတင်ဘွတ်ကင်တင်ခြင်း) နဲ့ Session (အမှန်တကယ်ဆော့နေတဲ့ ကစားချိန်) နှစ်ခုကို ရောထွေးနေပါတယ်။ ဒီလိုခွဲထုတ်ဖို့ **အားလုံးပြောင်းရမယ့် အလုပ်ပမာဏက အင်မတန်ကြီးမားပါတယ်**။

### ဘာလို့ ခွဲသင့်တာလဲ
1. **Booking** = ကြိုတင်စာရင်းပေးခြင်း (Future reservation) — status: pending → confirmed → rejected/cancelled  
2. **Session** = အခုဆော့နေတဲ့အချိန် (Actual play time) — status: checked_in → Active → Done  
3. နှစ်ခုရောထားတော့ SQL query တွေ ရှုပ်တယ်၊ report တွေ မှားတယ်၊ status value တွေ မရှင်းဘူး  
4. Future feature အနေနဲ့ booking calendar, customer self-booking, analytics, စတာတွေ ဖြည့်မယ်ဆို ဒီအတိုင်းဆက်သုံးလို့မရ

### ဘာတွေ ထိခိုက်မလဲ (အနှစ်ချုပ်)
| Layer | Files Touched | ~Lines Changed | Risk |
|-------|--------------|---------------|------|
| Database Schema | 2 new tables, 1 migrated | ~100 lines DDL | MEDIUM |
| API Backend | 5 route files | ~3,000+ lines | HIGH |
| Sale Bot | 4 handler files | ~1,500+ lines | HIGH |
| Customer Bot | 2 files | ~500 lines | MEDIUM |
| Dashboard | 10 Vue views | ~800 lines | MEDIUM |
| Financial | 1 route file | ~200 lines | HIGH |
| Services | 4 files | ~300 lines | MEDIUM |
| **TOTAL** | **~28 files** | **~6,400+ lines** | **HIGH** |

**အချိန်ခန့်မှန်း:** 60-80 hours (မ 4-5 ပတ်ခန့် — 1 developer, full-time)

---

## 1. Current State — console_booking Table

### 1.1 Where the table lives
- **Database:** `psvibe_api` on MySQL (localhost)
- **Connection:** `mysql_db.py` wrapper → `_mysql_query`, `_mysql_exec`, `_mysql_query_one`
- **No ORM** — raw SQL strings everywhere (~292 `console_booking` references across Python codebase)

### 1.2 Columns (observed from usage)

| Column | Type | Booking Concern | Session Concern | Notes |
|--------|------|----------------|-----------------|-------|
| `id` | INT AUTO_INCREMENT | ✅ | ✅ | Primary key |
| `console_id` | VARCHAR | ✅ | ✅ | Linked console |
| `member_id` | VARCHAR | ✅ | ✅ | Member or Guest |
| `booking_date` | DATE | ✅ | ✅ | Date of play |
| `start_time` | DATETIME | ✅ (planned) | ✅ (actual) | Overloaded! |
| `end_time` | DATETIME | ✅ (planned) | ✅ (actual) | Overloaded! |
| `status` | VARCHAR | ✅ | ✅ | **OVERLOADED** — see below |
| `staff_name` | VARCHAR | ✅ | ⬜ | Customer name for bot bookings |
| `notes` | TEXT | ✅ | ✅ | General notes |
| `telegram_chat_id` | VARCHAR | ✅ | ⬜ | For notifications |
| `duration_mins` | INT | ✅ (planned) | ✅ (actual) | Overloaded! |
| `phone` | VARCHAR | ✅ | ⬜ | Customer phone |
| `game_name` | VARCHAR | ✅ | ✅ | Game being played |
| `created_at` | TIMESTAMP | ✅ | ✅ | Record creation |
| `cancelled_at` | TIMESTAMP | ✅ | ⬜ | When cancelled |
| `admin_notify_msg_id` | VARCHAR | ✅ | ⬜ | Telegram msg id |

### 1.3 Status Values — The Core Problem

The `status` column mixes booking lifecycle AND session lifecycle:

| Status | Type | Meaning | Used By |
|--------|------|---------|---------|
| `pending` | Booking | Customer submitted, needs staff approval | Customer Bot, Sale Bot |
| `confirmed` | Booking | Staff approved, waiting for time | Sale Bot, Dashboard |
| `rejected` | Booking | Staff rejected | Sale Bot, Dashboard |
| `cancelled` | Booking/Terminal | Booking was cancelled | Both Bots, Dashboard |
| `pending_check_in` | Booking→Session | Booking about to be checked in (Sale Bot) | Sale Bot |
| `checked_in` | Session | Customer arrived, NOT started yet | API, Sale Bot |
| `Active` | Session | Currently playing | Everything! |
| `Done` | Session/Terminal | Session completed | API, Sale Bot, Finance |
| `Waiting` | Booking/Waitlist | Waitlisted (special) | Waitlist feature |
| `Notified` | Booking/Waitlist | Waitlist notified (special) | Waitlist feature |

**Problem:** `start_time` gets overwritten from planned booking time to actual session start time during checkin. This loses the original booking time data!

### 1.4 Current Data Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Customer Bot   │────▶│   API Server     │────▶│   MySQL DB      │
│  (Telegram)     │     │   (FastAPI:8000) │     │   console_booking│
│                 │     │                  │     │                 │
│  POST /bookings │     │  booking_routes  │     │  status=pending │
│  (pending)      │     │  console_routes  │     │                 │
└─────────────────┘     │  patch_routes    │     └────────┬────────┘
                        │  dashboard_routes│              │
┌─────────────────┐     │                  │     ┌────────▼────────┐
│  Sale Bot       │────▶│  session_timer   │     │  console_status │
│  (Telegram)     │     │  console_status  │     │  (synced)       │
│                 │     │  digest_engine   │     │                 │
│  approve/reject │     │  daily_summary   │     │  status↔Free/   │
│  checkin/start  │     │  booking_reminder│     │  Active/Reserved│
│  extend/end     │     │                  │     └─────────────────┘
└─────────────────┘     └──────────────────┘
```

---

## 2. Conceptual Model — What Should Change

### 2.1 Proposed Separation

```
┌──────────────────────────────────────┐
│           console_bookings            │  NEW table (renamed)
│  ─────────────────────────────────── │
│  id, member_id, customer_name,       │
│  phone, telegram_chat_id,            │
│  console_id, console_type,           │
│  booking_date, planned_start,        │  NEW: planned times
│  planned_end, planned_duration,      │
│  game_name, status (booking only),   │  booking statuses only
│  created_at, cancelled_at, notes     │
└──────────────┬───────────────────────┘
               │ 1:1 or 1:0
┌──────────────▼───────────────────────┐
│           console_sessions            │  NEW table
│  ─────────────────────────────────── │
│  id, booking_id (FK, nullable),      │  links to booking
│  console_id, member_id,              │
│  actual_start, actual_end,           │  ACTUAL play times
│  actual_duration, status,            │  session statuses only
│  game_name, staff_name, notes,       │
│  created_at,                         │
│  linked_to_sale_id (FK, nullable)    │  links to sales_daily
└──────────────────────────────────────┘
```

### 2.2 Status Cleanup

| Old Status | New Table | New Status |
|-----------|-----------|------------|
| `pending` | `console_bookings` | `pending` |
| `confirmed` | `console_bookings` | `confirmed` |
| `rejected` | `console_bookings` | `rejected` |
| `cancelled` | `console_bookings` | `cancelled` |
| `pending_check_in` | `console_bookings` | `pending_check_in` (or just `confirmed`) |
| `Waiting`/`Notified` | `console_bookings` | `waiting`/`notified` |
| `checked_in` | `console_sessions` | `checked_in` |
| `Active` | `console_sessions` | `active` |
| `Done` | `console_sessions` | `done` |

### 2.3 Key Benefits
- Booking times NEVER get overwritten by session start
- Can have 1 booking → 0 sessions (no-show), 1 booking → 1 session (normal), or 0 bookings → 1 session (walk-in)
- Financial reconciliation gets its own `console_sessions.sale_id` link
- Analytics can separately track booking patterns vs actual play patterns

---

## 3. Database Impact

### 3.1 New Tables Required

**`console_bookings`** (renamed from `console_booking` with removed columns):
- Remove: `actual_start_time` concept (was `start_time` in session context)
- Remove: `actual_end_time` concept
- Keep: `planned_start_time`, `planned_end_time`, `planned_duration_mins`
- Keep: booking statuses only
- Keep: customer info, contact, game preference

**`console_sessions`** (entirely new):
- `id` INT AUTO_INCREMENT
- `booking_id` INT NULLABLE FK → console_bookings.id
- `console_id` VARCHAR
- `member_id` VARCHAR
- `actual_start_time` DATETIME
- `actual_end_time` DATETIME
- `actual_duration_mins` INT (computed or set)
- `status` ENUM('checked_in','active','done')
- `game_name`, `staff_name`, `notes`
- `linked_sale_id` INT NULLABLE FK → sales_daily.id
- `created_at` TIMESTAMP

### 3.2 Migration Complexity

**Phase 1: Data Audit** (4 hours)
- Count rows per status
- Identify orphan records (booking without sale, sale without booking)
- Backfill `planned_*` from current `start_time` for non-Active bookings

**Phase 2: Schema Migration** (6 hours)
- CREATE tables
- INSERT into `console_bookings` from existing non-session rows
- INSERT into `console_sessions` from Active/Done/checked_in rows
- Add foreign keys
- Migrate all related tables (food_cart, stock_hold, customer_feedback, console_status)

**Phase 3: RENAME old table** (2 hours)
- Rename `console_booking` → `console_booking_legacy`
- Verify all writes go to new tables
- Drop after 30 days

### 3.3 Related Tables Impact

| Table | Column | Change Needed |
|-------|--------|--------------|
| `food_cart` | `booking_id` → `session_id` | FK to sessions |
| `stock_hold` | `booking_id` → `session_id` | FK to sessions |
| `customer_feedback` | `booking_id` → `session_id` | FK to sessions |
| `sales_daily` | references console_booking via reconciliation | Add `session_id` |
| `console_status` | syncs from booking table | Sync from sessions instead |
| `admin_notify_msg_id` | on booking | Stays on bookings |

---

## 4. Code Impact Matrix

### 4.1 API Server (`/root/psvibe_api_server/`)

| File | Lines | Changes | Risk | Details |
|------|-------|---------|------|---------|
| `routes/booking_routes.py` | 1,775 | **HEAVY** | HIGH | Every endpoint touches console_booking; needs booking-only/session-only split |
| `routes/console_routes.py` | 969 | **HEAVY** | HIGH | `/consoles/start-session`, `/sessions/start`, `/sessions/move`, `/sessions/swap` |
| `patch_routes.py` | 1,408 | **HEAVY** | HIGH | Booking CRUD, waitlist, finance, status patch |
| `dashboard_routes.py` | 2,811 | **HEAVY** | HIGH | Console status, bookings CRUD, timer, feedback, members/transactions |
| `routes/finance_routes.py` | 2,054 | Medium | HIGH | Reconciliation view (line ~1668) queries console_booking |
| `session_timer.py` | ~300 | Medium | MEDIUM | Timer references booking_id → session_id |
| `console_status.py` | ~120 | Medium | MEDIUM | Sync logic references booking table |
| `digest_engine.py` | ~400 | Light | LOW | Cross-reference checks use console_booking |
| `daily_summary.py` | ~50 | Light | LOW | Summary queries console_booking |
| `app.py` | ~200 | Light | LOW | Bootstrap queries Active console_ids |

### 4.2 Sale Bot (`/root/psvibe-sales-bot/`)

| File | Lines | Changes | Risk | Details |
|------|-------|---------|------|---------|
| `bot/handlers/booking.py` | 1,736 | **HEAVY** | HIGH | Main booking handler — approve/reject/checkin/start/end all use console_booking |
| `bot/handlers/booking_flow.py` | 698 | **HEAVY** | HIGH | Booking flow state machine — status transitions |
| `bot/handlers/console_mgmt.py` | 523 | Medium | MEDIUM | Console management — active sessions display |
| `bot/handlers/sales.py` | ~800 | Medium | HIGH | Sales flow uses booking_id for food cart, payment, end session |
| `bot/api_client.py` | 1,371 | Medium | MEDIUM | API client calls — may need new endpoints |

### 4.3 Customer Bot (`/root/psvibe-sales-bot/customer_bot/`)

| File | Lines | Changes | Risk | Details |
|------|-------|---------|------|---------|
| `handlers.py` | ~1,000 | Medium | MEDIUM | My Bookings, cancel booking, search |
| `booking.py` | ~200 | Medium | MEDIUM | Booking display formatting |

### 4.4 Dashboard (`/root/psvibe-dashboard/src/`)

| View | Impact | Risk | Details |
|------|--------|------|---------|
| `BookingsManagement.vue` | **HEAVY** | MEDIUM | Full CRUD form, display, filters |
| `ConsoleTimer.vue` | **HEAVY** | MEDIUM | Timer extension, console swapping |
| `TimelineView.vue` | **HEAVY** | MEDIUM | Visual timeline of all bookings |
| `DashboardView.vue` | Light | LOW | StatsCard "Bookings Today" count |
| `ConsoleGrid.vue` | Light | LOW | Console status display |
| `TodaySchedule.vue` | Light | LOW | Today's schedule display |
| `FoodOrders.vue` | Medium | LOW | Groups by booking_id |
| `ReconciliationView.vue` | Medium | MEDIUM | Session-to-sale matching |
| `PredictiveAnalytics.vue` | Light | LOW | Peak hours from bookings |
| `FeedbackView.vue` | Light | LOW | Links to booking |
| `CustomerBotSuccess.vue` | Light | LOW | Booking success rate |
| `MembersManagement.vue` | Light | LOW | Member booking history |

---

## 5. API Endpoints — Migration Map

### 5.1 Booking-Only Endpoints (→ new table)

| Current Endpoint | Method | New Endpoint | Change |
|-----------------|--------|-------------|--------|
| `GET /api/bookings` | GET | `GET /api/bookings` | Now reads from `console_bookings` |
| `POST /api/bookings` | POST | Same | Creates booking row only |
| `GET /api/bookings/{id}` | GET | Same | Reads booking |
| `PATCH /api/bookings/{id}/status` | PATCH | Same | Approve/reject booking |
| `POST /api/bookings/cancel` | POST | Same | Cancel booking |
| `GET /api/bookings/broadcast-targets` | GET | Same | Telegram IDs from bookings |
| `GET /api/search-bookings` | GET | Same | Search by telegram_chat_id |
| `GET /api/available-slots` | GET | Same | Slot availability check |
| `POST /api/booking-conflicts` | POST | Same | Conflict detection |
| `POST /api/bookings/auto-cancel-no-show` | POST | Same | No-show cleanup |

### 5.2 Session-Only Endpoints (→ new table)

| Current Endpoint | Method | New Endpoint | Change |
|-----------------|--------|-------------|--------|
| `POST /api/consoles/start-session` | POST | Same | Creates session row, links booking |
| `POST /api/sessions/start` | POST | Same | Walk-in session, links checked_in booking |
| `POST /api/sessions/move` | POST | Same | Move between consoles |
| `POST /api/sessions/swap` | POST | Same | Swap two sessions |
| `POST /api/bookings/checkin` | POST | `POST /api/sessions/checkin` | Checkin → creates session |
| `PUT /api/end_booking/{id}` | PUT | `PUT /api/sessions/{id}/end` | End session |
| `POST /api/bookings/extend-duration` | POST | `POST /api/sessions/{id}/extend` | Extend session |

### 5.3 Hybrid Endpoints (need both tables)

| Current Endpoint | Method | Inferred Split |
|-----------------|--------|---------------|
| `GET /api/dashboard/consoles` | GET | Joins `console_status` + `console_sessions` |
| `GET /api/dashboard/schedule` | GET | Joins `console_sessions` |
| `GET /api/dashboard/bookings` | GET | Joins both tables for full view |
| `PUT /api/dashboard/bookings/{id}` | PUT | Split: edit booking vs edit session |
| `PUT /api/dashboard/bookings/{id}/timer` | PUT | Session-only now |
| `GET /api/members/{id}/transactions` | GET | Queries both bookings + sessions |
| `GET /api/dashboard/feedback` | GET | Joins sessions (was bookings) |

---

## 6. Bot Command Changes

### 6.1 Sale Bot Impact
- **Booking approval flow:** Unchanged (approve/reject booking)
- **Checkin flow:** `_do_checkin` marks session as `checked_in`; `_do_start_session` creates Active session
- **`/sessions` command:** Display active sessions from new table
- **Console menu:** Extend/End now target session_id instead of booking_id
- **Food cart:** `booking_id` references need to become `session_id`
- **Reminder system:** Booking reminders (before start) vs session reminders (before end)

### 6.2 Customer Bot Impact
- **New booking:** Unchanged (creates booking row)
- **My bookings:** Display from combined view (bookings + linked sessions)
- **Cancel booking:** Cancel booking only (sessions unaffected)
- **Feedback:** Links to session_id instead of booking_id

---

## 7. Dashboard View Impacts

### 7.1 Views That Break (Need Full Rewrites)
1. **BookingsManagement.vue** — All API calls, form fields, display columns
2. **ConsoleTimer.vue** — Timer targeting changes from booking to session
3. **TimelineView.vue** — Visual display from sessions table

### 7.2 Views That Need Partial Updates
4. **DashboardView.vue** — StatsCard count query
5. **ConsoleGrid.vue** — Active session display
6. **FoodOrders.vue** — Group by session_id
7. **ReconciliationView.vue** — Session-to-sale matching
8. **PredictiveAnalytics.vue** — Peak hours from sessions
9. **FeedbackView.vue** — Link to session_id
10. **CustomerBotSuccess.vue** — Booking success rate

---

## 8. Risk Assessment

### 8.1 HIGH Risks
1. **Data Integrity:** Migration must preserve all historical data exactly. Wrong backfill = lost history.
2. **Race Conditions:** All current code uses transactions + FOR UPDATE. Must maintain same level in new code.
3. **Financial Reconciliation:** Must not break. Sale ↔ Session matching must work post-migration.
4. **24/7 Operations:** PS VIBE runs daily. Migration must happen during off-hours and be reversible.

### 8.2 MEDIUM Risks
5. **Backward Compatibility:** Old API endpoints needed during transition. Versioned endpoints (`/v2/`) recommended.
6. **Bot State Machines:** Sale bot's booking flow has complex state; breaking it means customers can't play.
7. **Timer/Reminder Duplication:** Both API-level session_timer and bot-level _remind_loop must not double-fire.

### 8.3 LOW Risks
8. **Dashboard UI:** Mostly read-only displays — can show "no data" during migration.
9. **Analytics:** Peak hours, popular games — can recalculate after migration.

---

## 9. Migration Strategy — Phased Approach

### Phase 1: Schema & Audit (Week 1 — 12 hours)
1. Create migration scripts (DDL)
2. Run data audit on all 292 `console_booking` references
3. Create `console_bookings` and `console_sessions` tables
4. Write data backfill scripts
5. Test on staging/copy

### Phase 2: API Refactor (Week 2-3 — 30 hours)
1. Create new endpoint versions (`/v2/api/...`)
2. Refactor booking-only endpoints → book table
3. Refactor session-only endpoints → session table
4. Update hybrid endpoints to JOIN both
5. Add session_timer using session_id
6. Update console_status sync
7. Keep old endpoints running in parallel

### Phase 3: Bot Updates (Week 3 — 15 hours)
1. Update Sale Bot handlers to use new endpoints
2. Update Customer Bot
3. Test checkin/checkout flow end-to-end
4. Food cart integration test

### Phase 4: Dashboard (Week 4 — 15 hours)
1. Update all Vue views
2. Update API client calls
3. Test all views end-to-end

### Phase 5: Cleanup (Week 4-5 — 8 hours)
1. Drop old `console_booking` table (or rename to `_legacy`)
2. Remove deprecated endpoints
3. Regenerate analytics
4. Full system test
5. Documentation update

---

## 10. Effort Estimate

| Phase | Description | Hours | Who |
|-------|-------------|-------|-----|
| 1 | Schema & Audit | 12 | Backend |
| 2 | API Refactor | 30 | Backend |
| 3 | Bot Updates | 15 | Bot Dev |
| 4 | Dashboard | 15 | Frontend |
| 5 | Cleanup & Test | 8 | All |
| **TOTAL** | | **80 hours** | **~4-5 weeks** |

### Risk Buffer: +20 hours (100 total)
- Unexpected data issues
- Race condition bugs
- Rollback testing
- Documentation

---

## 11. Files Complete Reference

### API Server files touching `console_booking` (19 files):
1. `/root/psvibe_api_server/routes/booking_routes.py` — 1,775 lines
2. `/root/psvibe_api_server/routes/console_routes.py` — 969 lines
3. `/root/psvibe_api_server/patch_routes.py` — 1,408 lines
4. `/root/psvibe_api_server/dashboard_routes.py` — 2,811 lines
5. `/root/psvibe_api_server/routes/finance_routes.py` — 2,054 lines (reconciliation)
6. `/root/psvibe_api_server/routes/stock_routes.py` — (stock holds)
7. `/root/psvibe_api_server/routes/reports.py` — (reports)
8. `/root/psvibe_api_server/routes/botuser_routes.py` — (bot user stats)
9. `/root/psvibe_api_server/session_timer.py` — ~300 lines
10. `/root/psvibe_api_server/console_status.py` — ~120 lines
11. `/root/psvibe_api_server/digest_engine.py` — ~400 lines
12. `/root/psvibe_api_server/daily_summary.py` — ~50 lines
13. `/root/psvibe_api_server/app.py` — ~2 lines (bootstrap query)
14. `/root/psvibe_api_server/reconcile_consoles.py` — console reconciliation
15. `/root/psvibe_api_server/test_branch_filter.py` — test file

### Sale Bot files (4 files):
16. `/root/psvibe-sales-bot/bot/handlers/booking.py` — 1,736 lines
17. `/root/psvibe-sales-bot/bot/handlers/booking_flow.py` — 698 lines
18. `/root/psvibe-sales-bot/bot/handlers/console_mgmt.py` — 523 lines
19. `/root/psvibe-sales-bot/bot/handlers/sales.py` — ~800 lines (food cart)

### Customer Bot files (2 files):
20. `/root/psvibe-sales-bot/customer_bot/handlers.py` — ~1,000 lines
21. `/root/psvibe-sales-bot/customer_bot/booking.py` — ~200 lines

### Dashboard files (12 files):
22. `/root/psvibe-dashboard/src/views/BookingsManagement.vue`
23. `/root/psvibe-dashboard/src/views/ConsoleTimer.vue`
24. `/root/psvibe-dashboard/src/views/TimelineView.vue`
25. `/root/psvibe-dashboard/src/views/DashboardView.vue`
26. `/root/psvibe-dashboard/src/views/ConsoleManagement.vue`
27. `/root/psvibe-dashboard/src/views/FoodOrders.vue`
28. `/root/psvibe-dashboard/src/views/ReconciliationView.vue`
29. `/root/psvibe-dashboard/src/views/PredictiveAnalytics.vue`
30. `/root/psvibe-dashboard/src/views/FeedbackView.vue`
31. `/root/psvibe-dashboard/src/views/CustomerBotSuccess.vue`
32. `/root/psvibe-dashboard/src/views/MembersManagement.vue`
33. `/root/psvibe-dashboard/src/components/dashboard/TodaySchedule.vue`

### Total: ~33 files requiring changes

---

## 12. Recommendation

**ခွဲသင့်တယ်။ ဒါပေမယ့် major refactor ဖြစ်တဲ့အတွက်:**

1. **အခုလောလောဆယ် မလုပ်ပါနဲ့** — Revenue-generating system ကို risk ပေးဖို့ အဆင်မပြေသေးဘူး
2. **အရင်ဆုံး အပေါ်ယံ fix:** 
   - Stop overwriting `start_time` during checkin — add `actual_start_time` column instead
   - Add `planned_start_time` and `planned_end_time` columns to preserve booking times
   - This is ~4 hours work, low risk
3. **Full separation** ကိုတော့ 2026 Q3 ဒါမှမဟုတ် staff holiday season (Thingyan) မှာ downtime ရှိချိန်လုပ်သင့်
4. **Backup first** — Migration မလုပ်ခင် full DB dump ယူထားပါ

---

*End of Audit — Kora Subagent, 2026-07-01*
