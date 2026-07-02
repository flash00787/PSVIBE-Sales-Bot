# Booking vs Session — Error-Proof Implementation Plan
> **Version:** 2.0 — Error-Proof Edition  
> **Created:** 2026-07-02 | **Author:** Kora Subagent (DeepSeek Pro)  
> **Status:** ✅ Ready for Execution  
> **Prerequisite:** [booking-session-separation-audit.md](./booking-session-separation-audit.md)
>
> ⚠️ **CRITICAL:** Every step has BEFORE validation, AFTER validation, and ROLLBACK.  
> ⚠️ **Never skip a validation** — if BEFORE doesn't match expected, STOP and investigate.

---

## 📊 Verified Schema Reference (from SHOW CREATE TABLE 2026-07-02)

```
console_booking:
  id              INT AUTO_INCREMENT PK
  branch_id       INT NOT NULL DEFAULT '1'
  console_id      VARCHAR(20) DEFAULT NULL
  member_id       VARCHAR(50) DEFAULT NULL
  booking_date    DATE DEFAULT NULL
  start_time      DATETIME DEFAULT NULL
  end_time        DATETIME DEFAULT NULL
  status          VARCHAR(20) DEFAULT NULL
  staff_name      VARCHAR(100) DEFAULT NULL
  notes           TEXT
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  telegram_chat_id VARCHAR(50) DEFAULT ''
  duration_mins   INT DEFAULT 0
  phone           VARCHAR(50) DEFAULT ''
  game_name       VARCHAR(200) DEFAULT ''
  cancelled_at    DATETIME DEFAULT NULL
  admin_notify_msg_id VARCHAR(255) DEFAULT NULL
  AUTO_INCREMENT: 1241

Current row counts (2026-07-02):
  cancelled: 206 | confirmed: 9 | Done: 797 | rejected: 27
  TOTAL: 1,039 rows

Status values found in code (booking_routes.py + others):
  'pending'         — Customer submitted, needs approval
  'confirmed'       — Staff approved
  'rejected'        — Staff rejected
  'cancelled'       — Booking cancelled
  'pending_check_in'— Sale Bot intermediate state
  'Waiting'         — Waitlist (uppercase W!)
  'Notified'        — Waitlist notified (uppercase N!)
  'checked_in'      — Customer arrived, NOT playing yet
  'Active'          — Currently playing (uppercase A!)
  'Done'            — Completed (uppercase D!)

Dependent tables:
  food_cart.booking_id       VARCHAR(50)  — no FK, manual join
  stock_hold.booking_id      VARCHAR(64)  — no FK, manual join
  customer_feedback.booking_id VARCHAR(50) — no FK, manual join
  sales_daily                — NO booking_id column; reconciliation by console_id+time
  console_status             — synced from console_booking by sync_console_status()
```

---

## 🎯 Phase 0: Pre-Flight Checklist (30 min)

### Step 0.1: Verify system state BEFORE touching anything

```bash
# 0.1.1 — Check all services are running
systemctl is-active psvibe-api psvibe-sale-bot psvibe_customer_bot psvibe-analytics psvibe-attendance psvibe-discord-bot kora-host-api kora-voice

# EXPECTED: All 8 return "active"

# 0.1.2 — Full database backup
mysqldump -u psvibe_user -p'PsVibe@2026_Rotated!' --single-transaction --routines --triggers psvibe_api > /root/backups/pre-split-$(date +%Y%m%d-%H%M).sql 2>&1

# AFTER: Verify backup file
ls -lh /root/backups/pre-split-*.sql | tail -1
# EXPECTED: File size > 1MB (current DB is ~70+ tables with 1000+ rows)

# 0.1.3 — Snapshot current schema (ALL affected tables)
for TABLE in console_booking food_cart stock_hold customer_feedback sales_daily console_status; do
  echo "=== $TABLE ===" >> /root/backups/schema-snapshot-$(date +%Y%m%d).txt
  mysql -u psvibe_user -p'PsVibe@2026_Rotated!' psvibe_api -e "SHOW CREATE TABLE $TABLE\G" >> /root/backups/schema-snapshot-$(date +%Y%m%d).txt 2>&1
done

# AFTER: File exists and has 6 CREATE TABLE statements
wc -l /root/backups/schema-snapshot-$(date +%Y%m%d).txt
# EXPECTED: ~200-400 lines

# 0.1.4 — Row count snapshot (save for later comparison)
mysql -u psvibe_user -p'PsVibe@2026_Rotated!' psvibe_api -e "
  SELECT 'console_booking' as tbl, status, COUNT(*) as cnt FROM console_booking GROUP BY status
  UNION ALL SELECT 'food_cart', 'ALL', COUNT(*) FROM food_cart
  UNION ALL SELECT 'stock_hold', 'ALL', COUNT(*) FROM stock_hold
  UNION ALL SELECT 'customer_feedback', 'ALL', COUNT(*) FROM customer_feedback
  UNION ALL SELECT 'sales_daily', 'ALL', COUNT(*) FROM sales_daily
  UNION ALL SELECT 'console_status', 'ALL', COUNT(*) FROM console_status
  ORDER BY tbl, status;
" > /root/backups/row-counts-$(date +%Y%m%d).txt 2>&1

cat /root/backups/row-counts-$(date +%Y%m%d).txt
# EXPECTED: console_booking=1039, food_cart=349, stock_hold=236, customer_feedback=51, sales_daily=786, console_status=10

# 0.1.5 — Run existing test suite (19 tests)
cd /root/psvibe_api_server
source venv/bin/activate 2>/dev/null || true
python -m pytest tests/ -v 2>&1 | tee /root/backups/tests-before-$(date +%Y%m%d).log

# AFTER: Count passing tests
grep -c PASSED /root/backups/tests-before-$(date +%Y%m%d).log
# EXPECTED: 19 (all tests pass before migration)

# 0.1.6 — Confirm API is responding
curl -s http://localhost:8000/health | python3 -m json.tool
# EXPECTED: {"status": "ok", ...}

# 0.1.7 — Check current time in MMT (PS VIBE runs 9AM-9PM MMT)
python3 -c "from datetime import datetime, timezone, timedelta; mmt=timezone(timedelta(hours=6, minutes=30)); print(f'MMT: {datetime.now(mmt).strftime(\"%Y-%m-%d %H:%M\")}')"
# RULE: If MMT time is between 9:00 and 21:00 → DO NOT execute Phase 1 now. Wait for off-hours.
# RULE: Preferred execution window: 22:00-08:00 MMT (when lounge is closed)
```

**Phase 0 Gate:** ALL 7 steps above must pass before proceeding.
- ❌ Backup file missing or <1MB → STOP (disk space issue?)
- ❌ Tests don't all pass → STOP (broken before you started)
- ❌ Services not all active → STOP (system already degraded)
- ❌ MMT time is 9AM-9PM → STOP (lounge is open, wait)

---

## 🔧 Phase 1: Schema Migration (Micro-Steps with Validation)

### ⚠️ Maintenance Mode Decision
**Before Phase 1 Step 1.1:** Decide if you need maintenance mode:
- If lounge is CLOSED (22:00-08:00 MMT) → No maintenance mode needed (no customers)
- If lounge is OPEN but you have read-only mode → Enable read-only via API flag
- If lounge is OPEN and no read-only → **DO NOT PROCEED** — wait for off-hours

---

### Step 1.1: CREATE `console_bookings` table

```sql
-- BEFORE (validate table doesn't exist):
SHOW TABLES LIKE 'console_bookings';
-- EXPECTED: Empty set (0 rows)

-- EXECUTE:
CREATE TABLE console_bookings (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    branch_id       INT NOT NULL DEFAULT 1,
    console_id      VARCHAR(20) DEFAULT NULL,
    member_id       VARCHAR(50) DEFAULT NULL,
    booking_date    DATE DEFAULT NULL,
    planned_start   DATETIME DEFAULT NULL,
    planned_end     DATETIME DEFAULT NULL,
    planned_duration_mins INT DEFAULT 60,
    status          VARCHAR(20) DEFAULT 'pending',
    staff_name      VARCHAR(100) DEFAULT NULL,
    notes           TEXT,
    telegram_chat_id VARCHAR(50) DEFAULT '',
    phone           VARCHAR(50) DEFAULT '',
    game_name       VARCHAR(200) DEFAULT '',
    admin_notify_msg_id VARCHAR(255) DEFAULT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cancelled_at    DATETIME DEFAULT NULL,
    INDEX idx_console_bookings_status (status),
    INDEX idx_console_bookings_console (console_id),
    INDEX idx_console_bookings_date (booking_date),
    INDEX idx_console_bookings_phone (phone),
    INDEX idx_console_bookings_tg (telegram_chat_id),
    INDEX idx_console_bookings_status_date (status, booking_date),
    INDEX idx_console_bookings_branch (branch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- AFTER (validate table created with correct columns):
SHOW CREATE TABLE console_bookings\G
-- EXPECTED: Shows CREATE TABLE with all 17 columns + 7 indexes
-- Verify specific columns exist:
SELECT COUNT(*) as col_count FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA='psvibe_api' AND TABLE_NAME='console_bookings';
-- EXPECTED: 17

-- ROLLBACK: DROP TABLE IF EXISTS console_bookings;
```

### Step 1.2: CREATE `console_sessions` table

```sql
-- BEFORE (validate table doesn't exist):
SHOW TABLES LIKE 'console_sessions';
-- EXPECTED: Empty set

-- EXECUTE:
CREATE TABLE console_sessions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    branch_id       INT NOT NULL DEFAULT 1,
    booking_id      INT DEFAULT NULL,
    console_id      VARCHAR(20) NOT NULL,
    member_id       VARCHAR(50) DEFAULT 'Guest',
    actual_start    DATETIME NOT NULL,
    actual_end      DATETIME DEFAULT NULL,
    actual_duration_mins INT DEFAULT NULL,
    status          VARCHAR(20) DEFAULT 'checked_in',
    game_name       VARCHAR(200) DEFAULT NULL,
    staff_name      VARCHAR(100) DEFAULT NULL,
    notes           TEXT,
    linked_sale_id  INT DEFAULT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES console_bookings(id) ON DELETE SET NULL,
    INDEX idx_console_sessions_status (status),
    INDEX idx_console_sessions_console (console_id),
    INDEX idx_console_sessions_booking (booking_id),
    INDEX idx_console_sessions_status_console (status, console_id),
    INDEX idx_console_sessions_actual_start (actual_start),
    INDEX idx_console_sessions_branch (branch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- AFTER (validate table created):
SHOW CREATE TABLE console_sessions\G
-- EXPECTED: Shows CREATE TABLE with 14 columns + FK + 6 indexes
SELECT COUNT(*) as col_count FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA='psvibe_api' AND TABLE_NAME='console_sessions';
-- EXPECTED: 14

-- Verify FK exists:
SELECT CONSTRAINT_NAME, REFERENCED_TABLE_NAME FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA='psvibe_api' AND TABLE_NAME='console_sessions' AND REFERENCED_TABLE_NAME IS NOT NULL;
-- EXPECTED: 1 row → booking_id → console_bookings

-- ROLLBACK: DROP TABLE IF EXISTS console_sessions;
```

### Step 1.3: Add `session_id` columns to dependent tables

```sql
-- 1.3.1 — food_cart
-- BEFORE:
DESCRIBE food_cart;
-- EXPECTED: booking_id VARCHAR(50) exists, NO session_id column
ALTER TABLE food_cart ADD COLUMN session_id INT DEFAULT NULL AFTER booking_id;
-- AFTER:
DESCRIBE food_cart;
-- EXPECTED: booking_id then session_id columns
-- ROLLBACK: ALTER TABLE food_cart DROP COLUMN session_id;

-- 1.3.2 — stock_hold
-- BEFORE:
DESCRIBE stock_hold;
-- EXPECTED: booking_id VARCHAR(64) exists, NO session_id column
ALTER TABLE stock_hold ADD COLUMN session_id INT DEFAULT NULL AFTER booking_id;
-- AFTER:
DESCRIBE stock_hold;
-- EXPECTED: booking_id then session_id columns
-- ROLLBACK: ALTER TABLE stock_hold DROP COLUMN session_id;

-- 1.3.3 — customer_feedback
-- BEFORE:
DESCRIBE customer_feedback;
-- EXPECTED: booking_id VARCHAR(50) exists, NO session_id column
ALTER TABLE customer_feedback ADD COLUMN session_id INT DEFAULT NULL AFTER booking_id;
-- AFTER:
DESCRIBE customer_feedback;
-- EXPECTED: booking_id then session_id columns
-- ROLLBACK: ALTER TABLE customer_feedback DROP COLUMN session_id;

-- 1.3.4 — sales_daily (NEW column for direct session linking)
-- BEFORE:
DESCRIBE sales_daily;
-- EXPECTED: NO session_id column
ALTER TABLE sales_daily ADD COLUMN session_id INT DEFAULT NULL AFTER console_id;
ALTER TABLE sales_daily ADD INDEX idx_sales_session (session_id);
-- AFTER:
DESCRIBE sales_daily;
-- EXPECTED: session_id column exists after console_id
-- ROLLBACK: ALTER TABLE sales_daily DROP INDEX idx_sales_session; ALTER TABLE sales_daily DROP COLUMN session_id;
```

**Phase 1 Gate:** All 4 CREATE/ALTER statements above must succeed.
- ❌ Any SQL error → ROLLBACK ALL, investigate
- ✅ All 4 passed → Proceed to Phase 2

---

## 📦 Phase 2: Data Migration (Micro-Steps with Row-Count Validation)

### ⚠️ Read-Only Enforcement (Optional but Recommended)
If lounge is open, put API in read-only mode:
```bash
# Create a marker file
touch /tmp/PSVIBE_READONLY_MODE
# API should check this file and reject writes (implemented in Phase 3)
```

---

### Step 2.1: Migrate PURE BOOKING rows → console_bookings

**Booking-only statuses:** `pending`, `confirmed`, `rejected`, `cancelled`, `pending_check_in`, `Waiting`, `Notified`

```sql
-- BEFORE (count what we're about to migrate):
SELECT status, COUNT(*) as cnt FROM console_booking 
WHERE status IN ('pending','confirmed','rejected','cancelled','pending_check_in','Waiting','Notified')
GROUP BY status ORDER BY status;
-- EXPECTED (2026-07-02): cancelled=206, confirmed=9, rejected=27 (no pending/checked_in/Waiting/Notified currently)
-- SAVE THIS OUTPUT for AFTER comparison

-- EXECUTE:
INSERT INTO console_bookings (
    id, branch_id, console_id, member_id, booking_date,
    planned_start, planned_end, planned_duration_mins,
    status, staff_name, notes, telegram_chat_id, phone, game_name,
    admin_notify_msg_id, created_at, cancelled_at
)
SELECT
    id, branch_id, console_id, member_id, booking_date,
    start_time AS planned_start,
    end_time   AS planned_end,
    duration_mins AS planned_duration_mins,
    CASE
        WHEN status = 'Waiting' THEN 'waiting'
        WHEN status = 'Notified' THEN 'notified'
        ELSE status
    END AS status,
    staff_name, notes, telegram_chat_id, phone, game_name,
    admin_notify_msg_id, created_at, cancelled_at
FROM console_booking
WHERE status IN ('pending','confirmed','rejected','cancelled','pending_check_in','Waiting','Notified');

-- AFTER (validate counts match):
SELECT 'SOURCE' as src, status, COUNT(*) as cnt FROM console_booking 
WHERE status IN ('pending','confirmed','rejected','cancelled','pending_check_in','Waiting','Notified')
GROUP BY status
UNION ALL
SELECT 'DEST' as src, status, COUNT(*) as cnt FROM console_bookings
GROUP BY status
ORDER BY src, status;
-- EXPECTED: SOURCE and DEST counts match for each status

-- Also verify total:
SELECT (SELECT COUNT(*) FROM console_booking WHERE status IN ('pending','confirmed','rejected','cancelled','pending_check_in','Waiting','Notified')) as source_count,
       (SELECT COUNT(*) FROM console_bookings) as dest_count;
-- EXPECTED: source_count = dest_count

-- ROLLBACK: DELETE FROM console_bookings;
```

### Step 2.2: Migrate SESSION rows → console_sessions

**Session statuses:** `checked_in`, `Active`, `Done`

```sql
-- BEFORE (count what we're about to migrate):
SELECT status, COUNT(*) as cnt FROM console_booking 
WHERE status IN ('checked_in','Active','Done')
GROUP BY status ORDER BY status;
-- EXPECTED (2026-07-02): Done=797 (no checked_in or Active currently)
-- SAVE THIS OUTPUT

-- EXECUTE:
INSERT INTO console_sessions (
    booking_id, branch_id, console_id, member_id,
    actual_start, actual_end, actual_duration_mins,
    status, game_name, staff_name, notes, created_at
)
SELECT
    id AS booking_id,
    branch_id,
    console_id,
    member_id,
    start_time AS actual_start,
    end_time   AS actual_end,
    duration_mins AS actual_duration_mins,
    CASE
        WHEN status = 'Active' THEN 'active'
        WHEN status = 'Done' THEN 'done'
        WHEN status = 'checked_in' THEN 'checked_in'
        ELSE LOWER(status)
    END AS status,
    game_name, staff_name, notes, created_at
FROM console_booking
WHERE status IN ('checked_in','Active','Done');

-- AFTER (validate counts match):
SELECT 'SOURCE' as src, status, COUNT(*) as cnt FROM console_booking 
WHERE status IN ('checked_in','Active','Done')
GROUP BY status
UNION ALL
SELECT 'DEST' as src, status, COUNT(*) as cnt FROM console_sessions
GROUP BY status
ORDER BY src, status;
-- EXPECTED: SOURCE and DEST counts match for each status (adjusted for case)

-- ROLLBACK: DELETE FROM console_sessions;
```

### Step 2.3: Create BOOKING rows for Done/Active sessions (backfill)

**ရှင်းပြချက်:** Done/Active sessions had a booking before they became a session. We must create their booking records in `console_bookings` too, or the `booking_id` FK in `console_sessions` would be orphan.

```sql
-- BEFORE (check how many session rows have NO corresponding booking):
SELECT COUNT(*) as sessions_without_booking 
FROM console_sessions cs
LEFT JOIN console_bookings cb ON cs.booking_id = cb.id
WHERE cb.id IS NULL;
-- EXPECTED (2026-07-02): 797 (all Done sessions have no booking yet — we migrated them as sessions)

-- EXECUTE:
INSERT INTO console_bookings (
    id, branch_id, console_id, member_id, booking_date,
    planned_start, planned_end, planned_duration_mins,
    status, staff_name, notes, telegram_chat_id, phone, game_name,
    admin_notify_msg_id, created_at, cancelled_at
)
SELECT
    cb_orig.id, cb_orig.branch_id, cb_orig.console_id, cb_orig.member_id, cb_orig.booking_date,
    cb_orig.start_time AS planned_start,
    cb_orig.end_time   AS planned_end,
    cb_orig.duration_mins AS planned_duration_mins,
    'confirmed' AS status,
    cb_orig.staff_name, cb_orig.notes, cb_orig.telegram_chat_id, cb_orig.phone, cb_orig.game_name,
    cb_orig.admin_notify_msg_id, cb_orig.created_at, NULL
FROM console_booking cb_orig
WHERE cb_orig.status IN ('checked_in','Active','Done')
  AND cb_orig.id NOT IN (SELECT id FROM console_bookings);

-- AFTER (validate no orphan sessions):
SELECT COUNT(*) as orphan_sessions
FROM console_sessions cs
LEFT JOIN console_bookings cb ON cs.booking_id = cb.id
WHERE cb.id IS NULL;
-- EXPECTED: 0 (no orphan sessions)

-- Also validate booking count now includes Done/Active bookings:
SELECT status, COUNT(*) as cnt FROM console_bookings GROUP BY status ORDER BY status;
-- EXPECTED: 'confirmed' count should have increased by 797 (Done+Active sessions)

-- Validate total row count integrity:
SELECT 
  (SELECT COUNT(*) FROM console_booking) as original_total,
  (SELECT COUNT(*) FROM console_bookings) as new_bookings_total,
  (SELECT COUNT(*) FROM console_sessions) as sessions_total;
-- EXPECTED: new_bookings_total + sessions_total = original_total + (Done+Active) 
-- Explanation: Done/Active rows appear in BOTH tables (booking + session), 
-- so new_bookings_total should be original_total (since we migrated ALL rows to bookings, 
-- and sessions are the subset that had session data)

-- ROLLBACK: 
-- DELETE FROM console_bookings WHERE id IN (SELECT id FROM console_booking WHERE status IN ('checked_in','Active','Done'));
-- Then DELETE FROM console_sessions WHERE booking_id IN (SELECT id FROM console_booking WHERE status IN ('checked_in','Active','Done'));
```

### Step 2.4: Backfill `session_id` in dependent tables

**ရှင်းပြချက်:** `food_cart.booking_id`, `stock_hold.booking_id`, and `customer_feedback.booking_id` store the booking ID as VARCHAR. We now have `console_sessions.id` (INT) that we need to link. We match by joining through `console_sessions.booking_id`.

```sql
-- 2.4.1 — food_cart backfill
-- BEFORE:
SELECT COUNT(*) as food_cart_rows FROM food_cart;
-- EXPECTED: 349
SELECT COUNT(*) as food_cart_session_null FROM food_cart WHERE session_id IS NULL;
-- EXPECTED: 349 (all NULL initially)

-- EXECUTE:
UPDATE food_cart fc
JOIN console_sessions cs ON CAST(cs.booking_id AS CHAR) = fc.booking_id
SET fc.session_id = cs.id
WHERE fc.session_id IS NULL;

-- AFTER:
SELECT COUNT(*) as food_cart_linked FROM food_cart WHERE session_id IS NOT NULL;
-- EXPECTED: Should match number of food_cart rows linked to Done/Active sessions
-- Some food_cart rows may have booking_ids for pure bookings (pending/confirmed) 
-- that don't have sessions yet. That's OK — they stay session_id=NULL until session is created.

-- ROLLBACK: UPDATE food_cart SET session_id = NULL;

-- 2.4.2 — stock_hold backfill
-- BEFORE:
SELECT COUNT(*) as sh_session_null FROM stock_hold WHERE session_id IS NULL;
-- EXPECTED: 236 (all NULL)

-- EXECUTE:
UPDATE stock_hold sh
JOIN console_sessions cs ON CAST(cs.booking_id AS CHAR) = sh.booking_id
SET sh.session_id = cs.id
WHERE sh.session_id IS NULL;

-- AFTER:
SELECT COUNT(*) as sh_linked FROM stock_hold WHERE session_id IS NOT NULL;
-- ROLLBACK: UPDATE stock_hold SET session_id = NULL;

-- 2.4.3 — customer_feedback backfill
-- BEFORE:
SELECT COUNT(*) as cf_session_null FROM customer_feedback WHERE session_id IS NULL;
-- EXPECTED: 51 (all NULL)

-- EXECUTE:
UPDATE customer_feedback cf
JOIN console_sessions cs ON CAST(cs.booking_id AS CHAR) = cf.booking_id
SET cf.session_id = cs.id
WHERE cf.session_id IS NULL;

-- AFTER:
SELECT COUNT(*) as cf_linked FROM customer_feedback WHERE session_id IS NOT NULL;
-- ROLLBACK: UPDATE customer_feedback SET session_id = NULL;
```

### Step 2.5: FINAL DATA INTEGRITY CHECK (Pass/Fail Gate)

```sql
-- Check 1: Total rows in console_bookings = total rows in console_booking
SELECT 
  (SELECT COUNT(*) FROM console_booking) as legacy_count,
  (SELECT COUNT(*) FROM console_bookings) as new_bookings_count;
-- EXPECTED: legacy_count = new_bookings_count (both = 1039)

-- Check 2: Sessions count = Done + Active + checked_in from original
SELECT 
  (SELECT COUNT(*) FROM console_booking WHERE status IN ('checked_in','Active','Done')) as legacy_session_count,
  (SELECT COUNT(*) FROM console_sessions) as new_sessions_count;
-- EXPECTED: legacy_session_count = new_sessions_count (both = 797)

-- Check 3: No orphan sessions (every session has a booking)
SELECT COUNT(*) as orphans FROM console_sessions WHERE booking_id NOT IN (SELECT id FROM console_bookings);
-- EXPECTED: 0

-- Check 4: All 10 possible statuses accounted for
SELECT 'bookings' as tbl, status, COUNT(*) as cnt FROM console_bookings GROUP BY status
UNION ALL
SELECT 'sessions' as tbl, status, COUNT(*) as cnt FROM console_sessions GROUP BY status
ORDER BY tbl, status;
-- Review manually: ensure no unexpected status values

-- Check 5: Verify sample row integrity (spot-check 5 random IDs)
SELECT cb_leg.id, cb_leg.status as old_status, cb_leg.start_time, cb_leg.end_time, cb_leg.duration_mins,
       cb_new.planned_start, cb_new.planned_end, cb_new.planned_duration_mins, cb_new.status as new_booking_status,
       cs.actual_start, cs.actual_end, cs.actual_duration_mins, cs.status as new_session_status
FROM console_booking cb_leg
LEFT JOIN console_bookings cb_new ON cb_leg.id = cb_new.id
LEFT JOIN console_sessions cs ON cb_leg.id = cs.booking_id
ORDER BY RAND() LIMIT 5;
-- Manually verify: planning times match, status mappings correct

-- Check 6: Verify branch_id preserved
SELECT branch_id, COUNT(*) FROM console_bookings GROUP BY branch_id;
SELECT branch_id, COUNT(*) FROM console_sessions GROUP BY branch_id;
-- EXPECTED: All rows have branch_id=1 (current single-branch setup)
```

**Phase 2 Gate:** ALL 6 integrity checks must pass.
- ❌ Any check fails → ROLLBACK ALL (DELETE FROM console_bookings; DELETE FROM console_sessions; ALTER TABLE ... DROP COLUMN session_id on 4 tables)
- ✅ All checks pass → Proceed to Phase 2.6

### Step 2.6: Rename legacy table

```sql
-- BEFORE:
SHOW TABLES LIKE 'console_booking';
-- EXPECTED: console_booking
SHOW TABLES LIKE 'console_booking_legacy';
-- EXPECTED: Empty set

-- EXECUTE:
ALTER TABLE console_booking RENAME TO console_booking_legacy;

-- AFTER:
SHOW TABLES LIKE 'console_booking';
-- EXPECTED: Empty set
SHOW TABLES LIKE 'console_booking_legacy';
-- EXPECTED: console_booking_legacy

-- Also verify new tables are intact:
SELECT COUNT(*) as cnt FROM console_bookings;
SELECT COUNT(*) as cnt FROM console_sessions;
-- EXPECTED: 1039 and 797

-- ROLLBACK: ALTER TABLE console_booking_legacy RENAME TO console_booking;
-- (Note: you can keep console_bookings + console_sessions — they just won't be used)

-- ⚡ SMOKE TEST — Can we query new tables?
SELECT * FROM console_bookings LIMIT 1;
SELECT * FROM console_sessions LIMIT 1;
-- EXPECTED: 1 row each
```

---

## 🔄 Phase 3: API Dual-Write Mode (Parallel Verification)

### Concept: 24-Hour Dual-Write Window

**ရှင်းပြချက်:** Code ကို တစ်ခါတည်းပြောင်းမယ့်အစား old table နဲ့ new table နှစ်ခုလုံးကို တပြိုင်နက် write လုပ်မယ်။ 24 နာရီကြာအောင် old ရော new ရော ရေးပြီး data discrepancy မရှိမှ new table only ကိုပြောင်းမယ်။ ဒါက error rate ကို 0% အထိ လျှော့ချပေးတယ်။

### Architecture: API Request → Write Both Tables → Compare Later

```
┌──────────────┐     ┌─────────────────────┐
│  Sale Bot    │────▶│  POST /api/bookings │
│  Customer Bot│     │                     │
│  Dashboard   │     │  ┌─────────────────┐│
└──────────────┘     │  │ DUAL WRITE      ││
                     │  │ 1. console_     ││
                     │  │    booking_legacy││
                     │  │ 2. console_     ││
                     │  │    bookings     ││
                     │  │ 3. console_     ││
                     │  │    sessions     ││
                     │  └─────────────────┘│
                     │                     │
                     │  GET /api/bookings  │← Reads from NEW tables only
                     └─────────────────────┘
```

### Step 3.1: Create dual-write utility module

**File:** `/root/psvibe_api_server/dual_write.py`

```python
"""
Dual-Write Utility for Booking-Session Split Migration

During transition (24hr window), writes go to BOTH legacy and new tables.
Reads come from new tables only. After 24hr with 0 discrepancies, 
switch to new-tables-only mode.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger("psvibe_api.dual_write")

# ═══════════════════════════════════════════════════════════════
# HEALTH-CHECK: Compare legacy vs new table row counts
# ═══════════════════════════════════════════════════════════════

def get_discrepancy_report(mysql_query_func) -> Dict[str, Any]:
    """
    Compare legacy vs new tables. Returns discrepancies (should be empty).
    Called by /api/health/dual-write-status endpoint.
    """
    discrepancies = []
    
    # Compare booking counts (legacy vs new bookings table)
    legacy_count = mysql_query_func("SELECT COUNT(*) as cnt FROM console_booking_legacy")[0]["cnt"]
    new_bookings_count = mysql_query_func("SELECT COUNT(*) as cnt FROM console_bookings")[0]["cnt"]
    if legacy_count != new_bookings_count:
        discrepancies.append({
            "type": "booking_count",
            "legacy": legacy_count,
            "new": new_bookings_count,
            "diff": new_bookings_count - legacy_count
        })
    
    # Compare session counts (Done+Active+checked_in from legacy vs sessions)
    legacy_session_count = mysql_query_func(
        "SELECT COUNT(*) as cnt FROM console_booking_legacy WHERE status IN ('checked_in','Active','Done')"
    )[0]["cnt"]
    new_sessions_count = mysql_query_func("SELECT COUNT(*) as cnt FROM console_sessions")[0]["cnt"]
    if legacy_session_count != new_sessions_count:
        discrepancies.append({
            "type": "session_count",
            "legacy": legacy_session_count,
            "new": new_sessions_count,
            "diff": new_sessions_count - legacy_session_count
        })
    
    # Compare by status
    legacy_by_status = mysql_query_func(
        "SELECT status, COUNT(*) as cnt FROM console_booking_legacy GROUP BY status"
    )
    new_by_status = mysql_query_func(
        "SELECT status, COUNT(*) as cnt FROM console_bookings GROUP BY status"
    )
    # Map to dict for comparison
    legacy_map = {row["status"]: row["cnt"] for row in legacy_by_status}
    new_map = {row["status"]: row["cnt"] for row in new_by_status}
    
    # Check each legacy status
    for status, cnt in legacy_map.items():
        mapped_status = status
        if status == "Waiting": mapped_status = "waiting"
        elif status == "Notified": mapped_status = "notified"
        if new_map.get(mapped_status, 0) != cnt:
            discrepancies.append({
                "type": f"status_{status}",
                "legacy": cnt,
                "new": new_map.get(mapped_status, 0)
            })
    
    return {
        "dual_write_active": True,
        "discrepancies": discrepancies,
        "ok": len(discrepancies) == 0,
        "checked_at": datetime.now().isoformat()
    }

# ═══════════════════════════════════════════════════════════════
# DUAL-WRITE HELPERS (used in API endpoints during transition)
# ═══════════════════════════════════════════════════════════════

def dual_write_booking(mysql_exec_func, booking_data: Dict[str, Any]) -> int:
    """
    Write a new booking to BOTH legacy and new tables.
    Returns new booking_id.
    """
    # ... implementation after Phase 3 approval
    pass

def dual_create_session(mysql_exec_func, session_data: Dict[str, Any]) -> int:
    """
    Create session in BOTH legacy (update status+start_time) and new (INSERT).
    Returns new session_id.
    """
    pass
```

**BEFORE creating the file:**
```bash
ls /root/psvibe_api_server/dual_write.py 2>/dev/null
# EXPECTED: No such file (file doesn't exist yet)
```

**AFTER creating:**
```bash
python3 -c "from dual_write import get_discrepancy_report; print('OK')"
# EXPECTED: OK (no import errors)
```

### Step 3.2: Add health-check endpoint for discrepancy monitoring

Add to `app.py` or `patch_routes.py`:

```python
# TEMPORARY: Dual-write health check (remove after Phase 3)
@router.get("/api/health/dual-write-status")
async def dual_write_status():
    """Compare legacy vs new table counts. 0 discrepancies = safe to switch."""
    try:
        from dual_write import get_discrepancy_report
        report = get_discrepancy_report(_mysql_query)
        return report
    except ImportError:
        return {"dual_write_active": False, "ok": True, "note": "dual_write module not loaded"}
```

### Step 3.3: Dual-Write in Critical Endpoints (ONE at a time)

For EACH endpoint, apply this pattern:

```
Step 3.3.N: [Endpoint Name]
  BEFORE: 
    - Read current code at [file:line]
    - Run curl test to confirm current behavior
  EXECUTE:
    - Add dual-write to BOTH legacy and new tables
    - Read from new tables only
  AFTER:
    - Run same curl test → same response
    - Check /api/health/dual-write-status → 0 discrepancies
  ROLLBACK:
    - git checkout [file]
    - systemctl restart psvibe-api
```

**Priority order (highest-risk first):**

| # | Endpoint | File | Line | Write Pattern | Risk |
|---|----------|------|------|--------------|------|
| 3.3.1 | POST `/api/bookings` (create) | `booking_routes.py` | ~1500 | INSERT legacy + INSERT console_bookings | MEDIUM |
| 3.3.2 | POST `/api/bookings/checkin` | `booking_routes.py` | ~208 | UPDATE legacy + INSERT console_sessions | HIGH |
| 3.3.3 | PATCH `/api/bookings/{id}/status` | `booking_routes.py` | ~330 | UPDATE legacy + UPDATE console_bookings + INSERT console_sessions (if Active) | HIGH |
| 3.3.4 | PUT `/api/end_booking/{id}` | `booking_routes.py` | ~871 | UPDATE legacy + UPDATE console_sessions | HIGH |
| 3.3.5 | POST `/api/sessions/start` | `console_routes.py` | ~280 | UPDATE/INSERT legacy + INSERT console_sessions | HIGH |
| 3.3.6 | POST `/api/bookings/extend-duration` | `booking_routes.py` | ~105 | UPDATE legacy + UPDATE console_sessions | MEDIUM |

### Step 3.4: 24-Hour Monitoring Protocol

```bash
# Run every 15 minutes for 24 hours:
curl -s http://localhost:8000/api/health/dual-write-status | python3 -m json.tool

# EXPECTED: {"dual_write_active": true, "discrepancies": [], "ok": true}

# If ANY discrepancy appears:
# 1. PAUSE all dual-write
# 2. Compare the specific rows that differ
# 3. Fix the dual-write logic
# 4. Re-run migration from Phase 2 to reset new tables
# 5. Resume dual-write

# After 24 hours with 0 discrepancies → Gate passed → Phase 4
```

**Phase 3 Gate:** 
- ✅ 24 hours elapsed with 0 discrepancies for ALL endpoints
- ❌ Any discrepancy → STOP, investigate, fix, reset, retry
- ✅ All 19 tests + manual booking flow test pass

---

## 🚀 Phase 4: API Full Switch (New Tables Only)

### ⚙️ Approach: Remove Dual-Write, Keep New Tables

Now that dual-write has proven correctness for 24 hours, we switch ALL reads and writes to new tables only. Legacy writes are removed.

### Step 4.1: Update `booking_routes.py` — Endpoint by Endpoint

For each endpoint, follow this exact pattern:

```
Step 4.1.N: [Endpoint Name]
  BEFORE:
    - Ensure dual-write has 0 discrepancies (from Phase 3)
    - Read current dual-write code
  EXECUTE:
    - Remove legacy table write/read
    - Keep only new-table operations
    - Use console_bookings for booking ops, console_sessions for session ops
  AFTER:
    - curl test the endpoint → correct response
    - INSERT a test row → verify it goes to new tables only
    - Run affected tests
  ROLLBACK:
    - git stash / git checkout [file]
    - systemctl restart psvibe-api
```

**Detailed endpoint migration:**

#### 4.1.1: POST `/api/bookings` (Create Booking) — line ~1216
```python
# BEFORE: Writes to console_booking (and console_bookings via dual-write)
# AFTER: Write to console_bookings ONLY
#
# SQL changes:
#   INSERT INTO console_booking (...) → INSERT INTO console_bookings (...)
#
# Column mapping:
#   start_time → planned_start
#   end_time   → planned_end
#   duration_mins → planned_duration_mins
#
# AFTER validation:
curl -X POST http://localhost:8000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{"console_id":"C-01","member_id":"TestUser","booking_date":"2026-07-02","start_time":"2026-07-02 14:00:00","duration_mins":60,"staff_name":"Test"}'
# EXPECTED: {"success": true, "booking_id": NNN}
# SQL: SELECT id, status, planned_start, planned_end FROM console_bookings WHERE id=NNN;
# EXPECTED: status=pending, planned_start filled
```

#### 4.1.2: GET `/api/bookings` (List Bookings) — line ~1523
```python
# BEFORE: SELECT FROM console_booking
# AFTER: SELECT FROM console_bookings LEFT JOIN console_sessions
#        to include session status in response
#
# New query:
#   SELECT cb.*, cs.id as session_id, cs.status as session_status,
#          cs.actual_start, cs.actual_end, cs.actual_duration_mins
#   FROM console_bookings cb
#   LEFT JOIN console_sessions cs ON cs.booking_id = cb.id
#   WHERE ...
#
# AFTER validation:
curl -s http://localhost:8000/api/bookings | python3 -m json.tool | head -20
# EXPECTED: Returns bookings with session_id field (NULL for pure bookings)
```

#### 4.1.3: GET `/api/bookings/{id}` (Single Booking) — line ~577
```python
# BEFORE: SELECT FROM console_booking WHERE id=%s
# AFTER: SELECT FROM console_bookings LEFT JOIN console_sessions WHERE cb.id=%s
# Column mapping in response:
#   start_time → planned_start (or keep as start_time for backward compat?)
#   Add: session: {id, status, actual_start, actual_end, actual_duration_mins}
```

#### 4.1.4: PATCH `/api/bookings/{id}/status` — line ~330
```python
# This is the MOST COMPLEX endpoint — handles approve, reject, cancel, checkin, session start
#
# BEFORE: All transitions update console_booking
# AFTER: Split by transition type:
#
#   Status 'confirmed' → UPDATE console_bookings SET status='confirmed'
#   Status 'rejected'  → UPDATE console_bookings SET status='rejected'
#   Status 'cancelled' → UPDATE console_bookings SET status='cancelled', cancelled_at=NOW()
#   Status 'Active'    → INSERT console_sessions (actual_start=NOW(), status='active')
#                        + UPDATE console_bookings (no change, stays 'confirmed' or 'checked_in')
#
#   For Active transition:
#     1. Read planned_start, planned_duration from console_bookings
#     2. INSERT INTO console_sessions (booking_id, console_id, member_id, 
#        actual_start, actual_duration_mins, status='active', ...)
#     3. UPDATE console_status (same as before)
```

#### 4.1.5: POST `/api/bookings/checkin` — line ~208
```python
# BEFORE: UPDATE console_booking SET status='checked_in' WHERE id=%s
# AFTER: INSERT INTO console_sessions (booking_id, console_id, member_id, 
#         actual_start=NOW(), status='checked_in', ...)
#        + (optionally) UPDATE console_bookings SET status='pending_check_in' → stays
#        Actually: booking stays as 'confirmed', session row created with 'checked_in'
#        
# Column: actual_start = now() (actual arrival time, NOT planned_start)
```

#### 4.1.6: PUT `/api/end_booking/{id}` — line ~871
```python
# BEFORE: UPDATE console_booking SET end_time=%s, status='Done' WHERE id=%s
# AFTER: UPDATE console_sessions SET actual_end=%s, status='done' WHERE booking_id=%s
#        + UPDATE console_status SET status='Free' ...
#        + Cancel stock_hold via session_id
```

#### 4.1.7: POST `/api/bookings/extend-duration` — line ~105
```python
# BEFORE: UPDATE console_booking SET duration_mins=..., end_time=... WHERE id=%s AND status='Active'
# AFTER: UPDATE console_sessions SET actual_duration_mins=..., actual_end=... WHERE id=%s AND status='active'
#        (find session_id from booking_id or pass session_id directly)
```

#### 4.1.8: GET `/api/available-slots` — line ~1175
```python
# BEFORE: SELECT FROM console_booking WHERE status IN (active/confirmed/pending...) 
#         AND start_time < X AND end_time > Y
# AFTER: Check BOTH tables:
#   console_bookings: status IN ('confirmed','pending','pending_check_in') 
#                    AND planned_start < X AND planned_end > Y
#   console_sessions: status IN ('active','checked_in') 
#                    AND actual_start < X AND (actual_end IS NULL OR actual_end > Y)
```

#### 4.1.9: POST `/api/bookings/cancel` — line ~1010
```python
# BEFORE: UPDATE console_booking SET status='cancelled' WHERE id=%s AND status NOT IN ('Active','Done')
# AFTER: UPDATE console_bookings SET status='cancelled', cancelled_at=NOW() WHERE id=%s
#        + Check console_sessions: if active session exists, end it first
#        + If session is active, require session end BEFORE booking cancel
```

#### 4.1.10: POST `/api/bookings/auto-cancel-no-show` — line ~1746
```python
# BEFORE: UPDATE console_booking SET status='cancelled' WHERE status='pending' AND created_at < X
# AFTER: UPDATE console_bookings SET status='cancelled', cancelled_at=NOW() 
#        WHERE status='pending' AND created_at < NOW() - INTERVAL 30 MINUTE
```

### Step 4.2: Update `console_routes.py` — Session Operations

#### 4.2.1: GET `/api/fetch_console_status` — line ~26
```python
# BEFORE: JOIN console_booking WHERE status='Active'
# AFTER: JOIN console_sessions WHERE status='active' (lowercase!)
# Column changes:
#   cb.id as booking_id → cs.id as session_id (+ cs.booking_id as booking_id)
#   cb.staff_name → cs.staff_name
#   cb.duration_mins → cs.actual_duration_mins
#   cb.start_time → cs.actual_start
```

#### 4.2.2: POST `/api/consoles/start-session` — line ~280
```python
# Creates session for checked-in booking (autocheckin flow)
# BEFORE: INSERT INTO console_booking (...) or UPDATE console_booking SET status='Active'
# AFTER: 
#   If linked_booking_id provided:
#     INSERT INTO console_sessions (booking_id, console_id, actual_start=NOW(), 
#       actual_duration_mins=..., status='active', ...)
#     UPDATE console_bookings SET status='confirmed' WHERE id=%s (booking confirmed, session started)
#   If no booking (walk-in):
#     INSERT INTO console_sessions (booking_id=NULL, console_id, actual_start=NOW(), 
#       status='active', ...)
```

#### 4.2.3: POST `/api/sessions/start` — line ~380
```python
# Walk-in session start (already different from 4.2.2?)
# BEFORE: INSERT/UPDATE console_booking
# AFTER: INSERT INTO console_sessions (booking_id=linked_booking_id or NULL, ...)
```

#### 4.2.4: POST `/api/sessions/move` — line ~552
```python
# BEFORE: SELECT ... FROM console_booking WHERE id=%s FOR UPDATE
# AFTER: SELECT ... FROM console_sessions WHERE id=%s FOR UPDATE
# Column: start_time → actual_start, duration_mins → actual_duration_mins
```

#### 4.2.5: POST `/api/sessions/swap` — line ~664
```python
# Same as move — change table to console_sessions
# Column: start_time → actual_start, duration_mins → actual_duration_mins
```

### Step 4.3: Update `patch_routes.py` — Booking CRUD + Waitlist + Food

```python
# Summary: All console_booking references → console_bookings for booking operations
# Waitlist: status='Waiting'/'Notified' → status='waiting'/'notified' in console_bookings
# Food cart: booking_id → session_id (where available)
```

**Key endpoints in patch_routes.py:**

| Line Range | Endpoint | Change |
|-----------|----------|--------|
| ~128-200 | GET `/api/bookings` | `console_booking` → `console_bookings` LEFT JOIN `console_sessions` |
| ~215-260 | GET `/api/bookings/{id}` | Hybrid: booking + session info |
| ~253-390 | PUT `/api/bookings/{id}` | Split: edit booking in `console_bookings`, session in `console_sessions` |
| ~413-436 | PUT `/api/bookings/{id}/timer` | Session only → `console_sessions.actual_duration_mins` |
| ~453-465 | DELETE `/api/bookings/{id}` | Cancel booking in `console_bookings`; end session in `console_sessions` if exists |
| ~500-600 | Food cart endpoints | `booking_id` → `session_id` (dual support: try session_id, fallback to booking_id lookup) |
| ~800-900 | Waitlist endpoints | `status='Waiting'` → `'waiting'` in `console_bookings` |

### Step 4.4: Update `dashboard_routes.py` — Dashboard API

| Line Range | Endpoint | Change |
|-----------|----------|--------|
| ~30-50 | GET `/api/dashboard/consoles` | JOIN `console_sessions` instead of `console_booking` for active sessions |
| ~82-156 | GET `/api/dashboard/schedule` | `console_sessions` for active; `console_bookings` for upcoming |
| ~128-200 | GET `/api/dashboard/bookings` | Hybrid: LEFT JOIN `console_bookings` → `console_sessions` |
| ~253-390 | PUT `/api/dashboard/bookings/{id}` | Split edit: booking fields → `console_bookings`, timer → `console_sessions` |
| ~413-436 | PUT `/api/dashboard/bookings/{id}/timer` | `console_sessions.actual_duration_mins` |
| ~453-465 | DELETE `/api/dashboard/bookings/{id}` | Cancel booking + end session |
| ~194-200 | DELETE `/api/dashboard/bookings/cleanup` | Cleanup BOTH tables |
| ~1000+ | GET `/api/dashboard/members/{id}/transactions` | Query BOTH tables |
| ~1100+ | GET `/api/dashboard/feedback` | JOIN `console_sessions` |
| ~1200+ | GET `/api/dashboard/analytics/*` | `console_sessions` for actual play patterns |

### Step 4.5: Update `routes/finance_routes.py` — Reconciliation

```python
# BEFORE (line ~1668): FROM console_booking WHERE status='Done'
# AFTER: FROM console_sessions WHERE status='done'
#
# Column mapping:
#   cb.id as booking_id → cs.id as session_id (+ cs.booking_id)
#   cb.start_time → cs.actual_start
#   cb.end_time → cs.actual_end
#   cb.duration_mins → cs.actual_duration_mins
#   TIMESTAMPDIFF(cb.start_time, cb.end_time) → TIMESTAMPDIFF(cs.actual_start, cs.actual_end)
#
# The matching algorithm (console_id + mins ±10) stays the same.
```

### Step 4.6: Update `console_status.py` — Sync Logic

```python
# Query 1 (Active check): 
#   BEFORE: FROM console_booking WHERE console_id=%s AND status='Active'
#   AFTER:  FROM console_sessions WHERE console_id=%s AND status='active'
#   Column: start_time → actual_start, member_id → member_id
#
# Query 2 (Reserved check):
#   BEFORE: FROM console_booking WHERE console_id=%s AND status IN ('confirmed','checked_in') AND start_time <= ... AND end_time >= ...
#   AFTER: FROM console_bookings WHERE console_id=%s AND status IN ('confirmed','pending_check_in') AND planned_start <= ... AND planned_end >= ...
```

### Step 4.7: Update `session_timer.py` — Timer Module

```python
# Changes:
#   - _active_timers dict keyed by session_id (was booking_id)
#   - schedule_session_timer(session_id, ...) — param rename
#   - extend_session(session_id, extra_mins) — param rename
#   - end_session_now(session_id) — param rename
#   - All SQL: console_booking → console_sessions
#   - Column: start_time → actual_start, duration_mins → actual_duration_mins, end_time → actual_end
#   - resume_active_timers(): FROM console_sessions WHERE status='active'
```

### Step 4.8: Update `digest_engine.py`, `daily_summary.py`, `app.py`

```python
# digest_engine.py:
#   Line 216: FROM console_booking → FROM console_sessions
#   Line 527: Active session list → console_sessions
#   Line 542: Distinct consoles → console_sessions
#   Line 579: Utilization → console_sessions
#   Line 723/727: Active/Done counts → console_sessions
#   Line 754: Cross-reference → console_sessions
#
# daily_summary.py:
#   Line 24: FROM console_booking WHERE booking_date=%s 
#   → FROM console_bookings WHERE booking_date=%s (for booking counts)
#   + FROM console_sessions WHERE DATE(actual_start)=%s (for session counts)
#
# app.py:
#   Bootstrap query: console_booking WHERE status='Active' 
#   → console_sessions WHERE status='active'
```

### Step 4.9: Run Full Test Suite

```bash
# BEFORE running tests:
systemctl restart psvibe-api
sleep 3
curl -s http://localhost:8000/health | python3 -m json.tool
# EXPECTED: {"status":"ok"}

# RUN TESTS:
cd /root/psvibe_api_server
python -m pytest tests/ -v 2>&1 | tee /root/backups/tests-phase4-$(date +%Y%m%d).log

# AFTER: Count passes
grep -c PASSED /root/backups/tests-phase4-$(date +%Y%m%d).log
# EXPECTED: 19 (all tests pass)

# If any test fails:
grep FAILED /root/backups/tests-phase4-$(date +%Y%m%d).log
# Investigate and fix each failure
```

### Step 4.10: Manual Flow Test (curl-based)

```bash
# Test A: Create booking → approve → checkin → start → end
BOOKING_ID=$(curl -s -X POST http://localhost:8000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{"console_id":"C-01","member_id":"FlowTest","booking_date":"2026-07-02","start_time":"2026-07-02 14:00:00","duration_mins":60,"staff_name":"Test","source":"staff"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('booking_id',''))")

echo "Booking ID: $BOOKING_ID"
# EXPECTED: A numeric ID

# Approve
curl -s -X PATCH "http://localhost:8000/api/bookings/$BOOKING_ID/status" \
  -H "Content-Type: application/json" \
  -d '{"status":"confirmed"}' | python3 -m json.tool
# EXPECTED: {"success": true}

# Checkin
curl -s -X POST "http://localhost:8000/api/bookings/checkin" \
  -H "Content-Type: application/json" \
  -d "{\"booking_id\":$BOOKING_ID}" | python3 -m json.tool
# EXPECTED: {"success": true, "session_id": NNN}

# Start session (via console_routes)
curl -s -X POST http://localhost:8000/api/sessions/start \
  -H "Content-Type: application/json" \
  -d "{\"linked_booking_id\":$BOOKING_ID,\"console_id\":\"C-01\",\"member_id\":\"FlowTest\",\"duration_mins\":60}" \
  | python3 -m json.tool
# EXPECTED: {"success": true}

# End session
SESSION_ID=$(mysql -u psvibe_user -p'PsVibe@2026_Rotated!' psvibe_api -N -e "SELECT id FROM console_sessions WHERE booking_id=$BOOKING_ID")
curl -s -X PUT "http://localhost:8000/api/end_booking/$BOOKING_ID" | python3 -m json.tool
# EXPECTED: {"booking_id": NNN, "status": "Done"}

# Verify: booking still exists in console_bookings with status='confirmed'
mysql -u psvibe_user -p'PsVibe@2026_Rotated!' psvibe_api -e "SELECT id, status FROM console_bookings WHERE id=$BOOKING_ID"
# EXPECTED: status='confirmed' (booking was confirmed, session is done separately)

# Verify: session exists with status='done'
mysql -u psvibe_user -p'PsVibe@2026_Rotated!' psvibe_api -e "SELECT id, booking_id, status, actual_end FROM console_sessions WHERE booking_id=$BOOKING_ID"
# EXPECTED: status='done', actual_end IS NOT NULL
```

**Phase 4 Gate:**
- ✅ All 19 tests pass
- ✅ Full manual flow test passes (create → approve → checkin → start → end)
- ✅ Console freed after session end (console_status.status='Free')
- ✅ Dual-write discrepancy report shows 0 (no legacy writes happening)
- ❌ Any failure → ROLLBACK git checkout, restore DB, investigate

---

## 🤖 Phase 5: Bot Layer Updates

### ⚠️ Bot Architecture Note

Sale Bot and Customer Bot access data via HTTP API calls — NOT direct SQL. Since Phase 4 changed the API to return hybrid data, the bots mostly work as-is. However, some bot-side references to `booking_id` that should now be `session_id` need updating.

### Step 5.1: Sale Bot — `api_client.py`

```python
# Add new session-specific API helpers:

async def api_end_session_async(session_id: str) -> dict | None:
    """Async: End a session (previously end_booking)."""
    return await _api_call_async("PUT", f"sessions/{session_id}/end")

async def api_extend_session_async(session_id: str, extra_mins: int) -> dict | None:
    """Async: Extend a session."""
    return await _api_call_async("POST", f"sessions/{session_id}/extend", 
                                  json_data={"extra_mins": extra_mins})

# Keep old helpers for backward compat (they call API which handles table split internally):
# api_end_booking_async → still works (API endpoint maps booking_id → session_id)
# api_extend_duration → still works (API endpoint handles find session from booking)
```

**BEFORE:**
```bash
grep -c "def api_" /root/psvibe-sales-bot/bot/api_client.py
# EXPECTED: ~30 functions
```

**AFTER:**
```bash
python3 -c "from bot.api_client import api_end_session_async, api_extend_session_async; print('OK')"
# EXPECTED: OK
```

### Step 5.2: Sale Bot — `sales.py`

```python
# Key changes:
#
# 1. Food cart: booking_id → session_id
#    BEFORE: target.get("booking_id", "")
#    AFTER:  target.get("session_id") or target.get("booking_id", "")
#    (Fallback for backward compat during transition)
#
# 2. End session:
#    BEFORE: _mark_bk_completed() → calls api_end_booking_async(booking_id)
#    AFTER:  _mark_session_completed() → calls api_end_session_async(session_id)
#
# 3. Sale linking:
#    BEFORE: "booking_id": str(bk_id)
#    AFTER:  "session_id": str(session_id), "booking_id": str(bk_id)
#    (Send both during transition; API picks session_id)
```

**Specific line changes in sales.py:**

| Line | Current | New |
|------|---------|-----|
| ~164 | `booking_id = target.get("booking_id", "")` | `session_id = target.get("session_id") or target.get("booking_id", "")` |
| ~170 | `"booking_id": booking_id` | `"session_id": session_id, "booking_id": booking_id` |
| ~674 | `bk_id = active.get("booking_id", "")` | `session_id = active.get("session_id") or active.get("booking_id", "")` |
| ~1013 | `booking_id = context.user_data.get("booking_id", "")` | `session_id = context.user_data.get("session_id") or context.user_data.get("booking_id", "")` |
| ~1621 | `"booking_id": str(bk_id)` | `"session_id": str(session_id), "booking_id": str(bk_id)` |
| ~1632 | `_mark_bk_completed()` | `_mark_session_completed()` |

**Validation after each change:**
```bash
# Restart bot
systemctl restart psvibe-sale-bot
sleep 3
systemctl status psvibe-sale-bot | head -5
# EXPECTED: active (running)

# Test via Telegram (manual): 
# /start → Book → select console → enter time → confirm
# Staff: /checkin → /start → extend → end → food order → sale
```

### Step 5.3: Sale Bot — `booking_flow.py` and `console_mgmt.py`

```python
# booking_flow.py:
#   - Status transitions → API handles split (no internal SQL changes)
#   - Checkin: calls /api/bookings/checkin → API creates console_sessions row
#   - Start: calls /api/sessions/start → API creates session
#
# console_mgmt.py:
#   - /sessions command display → fetches from /api/fetch_console_status
#     (already returns session data from new table via Phase 4)
#   - Console menu extend/end → calls session-specific endpoints
#     Change: /api/bookings/extend-duration → /api/sessions/{session_id}/extend
```

### Step 5.4: Customer Bot — `handlers.py` and `booking.py`

```python
# handlers.py:
#   - cmd_book() → calls /api/bookings → unchanged
#   - cmd_my_bookings() → fetches /api/bookings → API returns hybrid (booking+session)
#   - cmd_cancel() → calls /api/bookings/cancel → unchanged
#   - Feedback flow → send session_id instead of booking_id
#
# booking.py:
#   - _format_booking() → API returns nested session object
#     Update to display: "Status: Confirmed | Playing" or "Status: Pending"
```

### Step 5.5: Bot Integration Test (Manual Flow via Telegram)

```
1. Customer Bot: /book → select console → time → confirm
   ✅ Booking appears in console_bookings (status=pending)

2. Sale Bot (staff): /confirmed → select booking → approve
   ✅ console_bookings.status = 'confirmed'

3. Sale Bot (staff): Checkin → mark customer arrived
   ✅ console_sessions row created (status=checked_in, booking_id=FK)

4. Sale Bot (staff): Start session → select console
   ✅ console_sessions.status = 'active', actual_start set
   ✅ console_bookings unchanged

5. Sale Bot (staff): Extend +30 min
   ✅ console_sessions.actual_duration_mins increased by 30

6. Sale Bot (staff): End session
   ✅ console_sessions.status = 'done', actual_end set
   ✅ console freed (console_status.status = 'Free')

7. Sale Bot (staff): Food order → complete sale
   ✅ food_cart.session_id linked
   ✅ sales_daily.session_id linked

8. Customer Bot: /mybookings → see history
   ✅ Shows past bookings + session details
```

**Phase 5 Gate:**
- ✅ Bot starts without errors
- ✅ Full booking-to-sale flow works
- ✅ Food cart links to session_id
- ✅ Sale completes with session_id
- ❌ Any step fails → git checkout + restart bot

---

## 📊 Phase 6: Dashboard Updates

### Step 6.1: `BookingsManagement.vue`

```vue
<!-- BEFORE: Fetches /api/dashboard/bookings (returns console_booking flat rows) -->
<!-- AFTER: Fetches /api/dashboard/bookings (returns hybrid: booking + session) -->

<!-- Key changes: -->
<!-- 1. Table columns: add "Session Status" column -->
<!-- 2. Row display: show booking status + session status -->
<!--    E.g., "Confirmed" (green) | "Playing" (blue) or "Done" (gray) -->
<!-- 3. Edit form: split into "Booking Info" + "Session Info" tabs -->
<!-- 4. Timer extension: use session_id from row.session.id -->
<!-- 5. End session button: call PUT /api/sessions/{session_id}/end -->
<!-- 6. Cancel button: only cancels booking (session continues if active) -->
```

**BEFORE validation:**
```bash
# Load BookingsManagement page in browser
# EXPECTED: Displays bookings with status column
```

**AFTER validation:**
```bash
# Reload page
# EXPECTED: 
#   - Shows "Session Status" column
#   - Active sessions show "Playing"
#   - Done sessions show "Completed"
#   - Pending bookings show "Pending"
#   - Edit modal has both booking and session sections
```

### Step 6.2: `ConsoleTimer.vue`

```vue
<!-- BEFORE: Timer uses booking_id, reads start_time + duration_mins from booking -->
<!-- AFTER: Timer uses session_id, reads actual_start + actual_duration_mins -->

<!-- Key changes: -->
<!-- 1. ID reference: booking_id → session_id -->
<!-- 2. Timer display: actual_start (start of actual play) -->
<!-- 3. Extend: POST /api/sessions/{session_id}/extend -->
<!-- 4. End: PUT /api/sessions/{session_id}/end -->
<!-- 5. Move/Swap: /api/sessions/move, /api/sessions/swap (paths unchanged) -->
```

### Step 6.3: `TimelineView.vue`

```vue
<!-- BEFORE: All entries from console_booking -->
<!-- AFTER: Two data sources:
     - Upcoming: console_bookings (confirmed, pending_check_in) → lighter color
     - Active: console_sessions (active) → solid/bold color
     - Past: console_sessions (done) → gray
-->

<!-- Visual distinction: -->
<!-- Booking bar: dashed border, lighter color, label "Booked" -->
<!-- Session bar: solid fill, bold color, label "Playing" or "Done" -->
```

### Step 6.4: Remaining Dashboard Views

| View | Change | Validation |
|------|--------|-----------|
| `DashboardView.vue` | StatsCard: "Active Sessions" from `console_sessions WHERE status='active'` | Count matches console grid |
| `ConsoleGrid.vue` | Data from `console_status` (already synced from sessions via Phase 4.6) | Shows correct status |
| `TodaySchedule.vue` | "Upcoming" from `console_bookings` (confirmed) | Shows correct bookings |
| `FoodOrders.vue` | Group by `session_id` (was `booking_id`) | Food orders group correctly |
| `ReconciliationView.vue` | Data from `console_sessions WHERE status='done'` (was `console_booking WHERE status='Done'`) | Matches sessions to sales |
| `FeedbackView.vue` | JOIN `customer_feedback.session_id → console_sessions.id` | Shows session context |
| `MembersManagement.vue` | History union of `console_bookings` + `console_sessions` | Shows all history |
| `PredictiveAnalytics.vue` | Peak hours from `console_sessions.actual_start` | Correct analytics |
| `CustomerBotSuccess.vue` | Booking stats from `console_bookings` | Correct stats |

### Step 6.5: Dashboard Rebuild & Test

```bash
# BEFORE rebuild — backup current dashboard
cp -r /root/psvibe-dashboard/src /root/backups/dashboard-src-$(date +%Y%m%d)
cp -r /root/psvibe-dashboard/dist /root/backups/dashboard-dist-$(date +%Y%m%d)

# Build
cd /root/psvibe-dashboard
npm run build 2>&1 | tail -20
# EXPECTED: Build successful, no errors

# Test: Load each view in browser
# 1. DashboardView → stats correct
# 2. BookingsManagement → hybrid display works
# 3. ConsoleTimer → timers show correct time
# 4. TimelineView → timeline renders
# 5. ConsoleGrid → console statuses correct
# 6. FoodOrders → grouped by session
# 7. ReconciliationView → matches correctly
# 8. FeedbackView → feedback loads
# 9. MembersManagement → history loads
# 10. PredictiveAnalytics → charts render

# ROLLBACK: cp -r /root/backups/dashboard-src-* /root/psvibe-dashboard/src; npm run build
```

**Phase 6 Gate:**
- ✅ Dashboard rebuilds without errors
- ✅ All 10 views load without console errors
- ✅ Bookings list shows both booking and session status
- ✅ Console timers work correctly
- ❌ Any view breaks → restore from backup

---

## 🧪 Phase 7: Integration Test & Cleanup

### Step 7.1: Full End-to-End Test (All Flows)

```bash
# Test 1: Booking → No-Show → Auto-Cancel
#   Create booking → wait 30min → auto-cancel runs
#   EXPECTED: console_bookings.status='cancelled', NO console_sessions row

# Test 2: Walk-in Session (No Booking)
#   Start session (no linked_booking_id) → play → end
#   EXPECTED: console_sessions row created (booking_id=NULL), status flows: active→done

# Test 3: Booking → Checkin → Abandon (No Session Start)
#   Create booking → confirm → checkin → never start → auto-cleanup
#   EXPECTED: console_bookings.status='confirmed', console_sessions.status='checked_in'
#   Cleanup should handle checked_in with no active session

# Test 4: Concurrent Sessions + Food Orders
#   Two active sessions on C-01, C-02 → add food to both → end both
#   EXPECTED: Each food_cart.session_id points to correct session

# Test 5: Move Between Consoles
#   Session C-01 active → move to C-03
#   EXPECTED: console_sessions.console_id updated to C-03
#   EXPECTED: console_status syncs correctly (C-01→Free, C-03→Active)

# Test 6: Swap Consoles
#   C-01 + C-02 active → swap
#   EXPECTED: Both sessions swap console_id
#   EXPECTED: console_status syncs correctly

# Test 7: Financial Reconciliation
#   Start sessions → make sales → run reconciliation
#   EXPECTED: Matches correct, no orphans, no missing

# Test 8: Customer Cancellation Mid-Session
#   Booking confirmed → session active → cancel booking
#   EXPECTED: Booking cancelled, session continues (booking_id FK ON DELETE SET NULL)
#   Or: Reject cancellation if session is active (design decision)

# Test 9: Dashboard All Views Load
#   EXPECTED: No errors, data consistent across all views

# Test 10: Test Suite
#   EXPECTED: 19/19 pass
```

### Step 7.2: 48-Hour Monitoring

```bash
# Monitor for 48 hours (2 full business days):
# 1. Check API error logs:
journalctl -u psvibe-api -f --since "48 hours ago" | grep -i "error\|exception" | wc -l
# EXPECTED: 0 new errors related to booking/session split

# 2. Check bot error logs:
journalctl -u psvibe-sale-bot -f --since "48 hours ago" | grep -i "error" | wc -l
# EXPECTED: 0 new errors

# 3. Check dual-write status (still running):
curl -s http://localhost:8000/api/health/dual-write-status
# EXPECTED: 0 discrepancies

# 4. Compare row counts each morning:
mysql -u psvibe_user -p'PsVibe@2026_Rotated!' psvibe_api -e "
  SELECT 'Bookings' as type, status, COUNT(*) FROM console_bookings GROUP BY status
  UNION ALL
  SELECT 'Sessions', status, COUNT(*) FROM console_sessions GROUP BY status
  ORDER BY type, status;
"
# Manually verify counts look reasonable for business activity
```

### Step 7.3: Migrate Dependent Tables to `session_id` Only

```sql
-- 7.3.1 — Verify all food_cart rows have session_id where possible
SELECT COUNT(*) as still_null FROM food_cart WHERE session_id IS NULL;
-- EXPECTED: Some rows may still be NULL (pure bookings without sessions yet)

-- 7.3.2 — Switch food cart reads to use session_id
-- (Phase 4.3 already did this, but verify)
-- Change API code: all food-cart reads use session_id, fallback to booking_id if NULL

-- 7.3.3 — Same for stock_hold
SELECT COUNT(*) as still_null FROM stock_hold WHERE session_id IS NULL;

-- 7.3.4 — Same for customer_feedback
SELECT COUNT(*) as still_null FROM customer_feedback WHERE session_id IS NULL;

-- 7.3.5 — Drop booking_id columns (ONLY after 48hr with 0 issues):
-- ⚠️ DO NOT DROP YET — keep for another week as safety net
-- ALTER TABLE food_cart DROP COLUMN booking_id;
-- ALTER TABLE stock_hold DROP COLUMN booking_id;
-- ALTER TABLE customer_feedback DROP COLUMN booking_id;
```

### Step 7.4: Drop Legacy Table (After 7 Days of Stable Operation)

```sql
-- BEFORE (verify 0 queries hit legacy table for 7 days):
-- Check slow query log or general log

-- EXECUTE:
DROP TABLE IF EXISTS console_booking_legacy;

-- AFTER:
SHOW TABLES LIKE 'console_booking_legacy';
-- EXPECTED: Empty set

-- Backup of legacy table still exists in Phase 0 backup:
-- /root/backups/pre-split-YYYYMMDD-HHMM.sql

-- ROLLBACK: Restore from Phase 0 backup
```

**Phase 7 Gate:**
- ✅ 10/10 integration tests pass
- ✅ 48 hours with 0 errors
- ✅ 19/19 tests continue passing
- ✅ Dashboard all views load correctly
- ❌ Any integration test fails → fix before proceeding

---

## 🚨 Emergency Rollback Procedures

### Full System Rollback (Any Phase)

```bash
# 1. Stop all services that touch the database
systemctl stop psvibe-api psvibe-sale-bot psvibe_customer_bot psvibe-analytics psvibe-attendance

# 2. Restore database from Phase 0 backup
mysql -u psvibe_user -p'PsVibe@2026_Rotated!' psvibe_api < /root/backups/pre-split-YYYYMMDD-HHMM.sql

# 3. Restore API code
cd /root/psvibe_api_server
git stash
git checkout main  # or the commit before migration started

# 4. Restore bot code
cd /root/psvibe-sales-bot
git stash
git checkout main

# 5. Restore dashboard
cp -r /root/backups/dashboard-src-YYYYMMDD/* /root/psvibe-dashboard/src/
cd /root/psvibe-dashboard && npm run build

# 6. Restart all services
systemctl start psvibe-api psvibe-sale-bot psvibe_customer_bot psvibe-analytics psvibe-attendance

# 7. Verify
sleep 3
systemctl is-active psvibe-api psvibe-sale-bot psvibe_customer_bot psvibe-analytics psvibe-attendance
# EXPECTED: All "active"
curl -s http://localhost:8000/health
# EXPECTED: {"status":"ok"}
```

### Partial Rollback (Phase-Specific)

| Phase | Rollback Time | Command |
|-------|-------------|---------|
| 1 (Schema) | 5 min | `DROP TABLE console_bookings; DROP TABLE console_sessions; ALTER TABLE {food_cart,stock_hold,customer_feedback,sales_daily} DROP COLUMN session_id;` |
| 2 (Migration) | 5 min | Same as Phase 1 + `ALTER TABLE console_booking_legacy RENAME TO console_booking;` |
| 3 (Dual-Write) | 5 min | `git checkout` API files; `systemctl restart psvibe-api` |
| 4 (API Switch) | 10 min | `git checkout` API files; restore DB from Phase 0 backup; `systemctl restart psvibe-api` |
| 5 (Bots) | 5 min | `git checkout` bot files; `systemctl restart psvibe-sale-bot psvibe_customer_bot` |
| 6 (Dashboard) | 10 min | Restore dashboard src from backup; rebuild |
| 7 (Cleanup) | 30 min | Full restore from Phase 0 backup |

---

## 📋 Summary: Key Files & Line Changes

### Database (4 objects created, 4 altered)
| Object | Action | Lines |
|--------|--------|-------|
| `console_bookings` | CREATE TABLE | ~25 |
| `console_sessions` | CREATE TABLE | ~25 |
| `food_cart.session_id` | ADD COLUMN | 1 |
| `stock_hold.session_id` | ADD COLUMN | 1 |
| `customer_feedback.session_id` | ADD COLUMN | 1 |
| `sales_daily.session_id` | ADD COLUMN | 1 |
| Migration SQL | INSERT/UPDATE | ~100 |

### API Server (9 files modified)
| File | ~Lines Changed | Risk |
|------|---------------|------|
| `routes/booking_routes.py` | ~600 | HIGH |
| `routes/console_routes.py` | ~400 | HIGH |
| `patch_routes.py` | ~500 | HIGH |
| `dashboard_routes.py` | ~500 | HIGH |
| `routes/finance_routes.py` | ~100 | MEDIUM |
| `session_timer.py` | ~150 | MEDIUM |
| `console_status.py` | ~60 | MEDIUM |
| `digest_engine.py` | ~100 | LOW |
| `daily_summary.py` | ~20 | LOW |
| `app.py` | ~5 | LOW |
| **NEW** `dual_write.py` | ~150 | N/A |

### Bot (3 files modified)
| File | ~Lines Changed | Risk |
|------|---------------|------|
| `bot/api_client.py` | ~30 | LOW |
| `bot/handlers/sales.py` | ~80 | HIGH |
| `bot/handlers/console_mgmt.py` | ~40 | MEDIUM |

### Dashboard (8 files modified)
| File | ~Lines Changed | Risk |
|------|---------------|------|
| `BookingsManagement.vue` | ~150 | MEDIUM |
| `ConsoleTimer.vue` | ~80 | MEDIUM |
| `TimelineView.vue` | ~60 | LOW |
| `DashboardView.vue` | ~20 | LOW |
| `FoodOrders.vue` | ~30 | LOW |
| `ReconciliationView.vue` | ~40 | MEDIUM |
| `FeedbackView.vue` | ~10 | LOW |
| `MembersManagement.vue` | ~20 | LOW |

**TOTAL: ~24 files, ~3,200 lines changed (reduced from original ~6,800 by leveraging dual-write)**

---

## ⏱ Time Estimate (Revised)

| Phase | Scope | Time |
|-------|-------|------|
| 0: Pre-Flight | Backup, validation | 30 min |
| 1: Schema | 2 CREATE + 4 ALTER | 1 hr |
| 2: Migration | 3 INSERT + backfill | 2 hr |
| 3: Dual-Write | Add dual-write module + 6 endpoints | 8 hr |
| 3.5: Monitor | 24hr wait with health checks | 24 hr (passive) |
| 4: API Switch | 9 files, remove dual-write | 16 hr |
| 5: Bot Updates | 3 files | 4 hr |
| 6: Dashboard | 8 Vue files | 8 hr |
| 7: Test & Cleanup | Integration testing + 48hr monitor | 8 hr |
| **TOTAL** | **Active work: ~47 hrs** | **~2 weeks part-time** |

---

## 🎯 Success Criteria (All Must Be Met)

1. ✅ Row counts match between old and new tables after migration
2. ✅ All 19 existing tests pass after each phase
3. ✅ Full booking-to-sale flow works (manual test)
4. ✅ Dual-write shows 0 discrepancies for 24 hours
5. ✅ Dashboard all 10 views load without errors
6. ✅ Financial reconciliation produces correct results
7. ✅ 48 hours of production monitoring with 0 new errors
8. ✅ Legacy table can be safely dropped (0 queries for 7 days)

---

## ⚠️ Critical Gotchas (From Code Inspection)

1. **`food_cart.booking_id` is VARCHAR — not INT!** The backfill uses `CAST(cs.booking_id AS CHAR)` for the JOIN. This is intentional.

2. **`stock_hold.booking_id` is VARCHAR(64)** — same pattern. DO NOT assume INT.

3. **`sales_daily` has NO booking_id column** — reconciliation is by `console_id + timestamp + mins matching`. The `session_id` column we added is new.

4. **`branch_id` exists on `console_booking`** — must be preserved in both new tables.

5. **Status case matters:** `'Active'` (capital A) in legacy vs `'active'` (lowercase) in new. Code must handle both during transition.

6. **`Waiting` and `Notified` are uppercase** in legacy table — our migration lowercases them to `waiting`/`notified` in new table.

7. **Timer module uses `booking_id` as dict key** — must change to `session_id` when switching to sessions table.

8. **Console_status sync** currently joins `console_booking WHERE status='Active'`. After switch, must join `console_sessions WHERE status='active'`. These run in DIFFERENT connections (console_status.py has its own `_MYSQL_CFG`).

9. **session_timer.py has its own MySQL connection** (doesn't use `mysql_db.py`). Check BOTH modules when updating SQL.

10. **The checkin endpoint (line 208) does NOT start a timer** — timer is handled by Sale Bot's `_remind_loop`. Don't accidentally add timer on checkin.

---

*End of Error-Proof Implementation Plan — Kora Subagent (DeepSeek Pro), 2026-07-02*
