# PS VIBE MySQL Database Schema

**Database:** `psvibe_api`  
**Host:** localhost (Docker container: `psvibe-mysql`)  
**Engine:** InnoDB (all tables)  
**Charset:** `utf8mb4` / `utf8mb4_unicode_ci`  
**Last Updated:** 2026-06-02 16:55 UTC

---

## Tables Overview

| #  | Table Name           | Description |
|----|----------------------|-------------|
| 1  | `accounts`           | Financial accounts (cash, bank, e-wallets) with current balances |
| 2  | `attendance_log`     | Staff login/logout attendance tracking |
| 3  | `card_wallet`        | Member card wallet snapshot (balance, tier, spend) |
| 4  | `console_booking`    | Game console bookings/reservations by members |
| 5  | `console_games`      | Games installed/available on each console |
| 6  | `console_status`     | Real-time status of each console (in-use, idle, etc.) |
| 7  | `finance_advances`   | Cash advances given to members |
| 8  | `finance_assets`     | Business asset purchases and valuations |
| 9  | `finance_opex_log`   | Operating expense transactions |
| 10 | `finance_payables`   | Money owed by the business to payees |
| 11 | `finance_prepaid`    | Prepaid expenses (paid in advance, pending settlement) |
| 12 | `finance_receivables`| Money owed to the business by payers |
| 13 | `games_library`      | Master library of all games (titles, genres, disc counts) |
| 14 | `inventory`          | Physical inventory items (categories, stock levels, pricing) |
| 15 | `member_wallets`     | Detailed member wallet records (minutes, spend, tier, referrals) |
| 16 | `members`            | Core member registration records |
| 17 | `promotions`         | Promotion/discount campaign definitions |
| 18 | `promotions_log`     | Audit log of promotion redemptions |
| 19 | `receipts`           | Payment receipts issued to members |
| 20 | `referral_log`       | Member referral tracking with rewards |
| 21 | `salary_advance`     | Salary advances paid to staff |
| 22 | `salary_payroll`     | Staff payroll records (salary, bonuses, deductions) |
| 23 | `sales_daily`        | Daily sales transactions (vouchers, discounts, net) |
| 24 | `settings`           | Legacy key-value application settings |
| 25 | `settings_config`    | Typed application configuration (strings, numbers, JSON, booleans) |
| 26 | `staff_records`      | Staff member records (salary, role, active status) |
| 27 | `staff_records_bak`  | Backup copy of staff_records |
| 28 | `stock_in`           | Inventory stock-in records (batches, costs) |
| 29 | `stock_out`          | Inventory stock-out/sales records |
| 30 | `sync_status`        | Google Sheets sync status tracker |
| 31 | `topup_log`          | Member top-up/balance-credit transaction log |

---

## Table Details

---

### `accounts`

**Purpose:** Tracks financial accounts (cash accounts, bank accounts, e-wallets) and their current balances.

| Column       | Type           | Null | Default    | Description |
|--------------|----------------|------|------------|-------------|
| `id`         | int            | NO   | auto-inc   | Primary key |
| `account_name` | varchar(100) | YES  | NULL       | Account display name |
| `account_type` | varchar(50)  | YES  | NULL       | Account category (e.g., cash, bank, e-wallet) |
| `balance`    | decimal(15,2)  | YES  | 0.00       | Current account balance |
| `notes`      | text           | YES  | NULL       | Additional notes |
| `updated_at` | timestamp      | YES  | CURRENT_TIMESTAMP | Auto-updated on change |

---

### `attendance_log`

**Purpose:** Records staff clock-in/clock-out times for attendance tracking and payroll.

| Column         | Type           | Null | Default    | Description |
|----------------|----------------|------|------------|-------------|
| `id`           | int            | NO   | auto-inc   | Primary key |
| `staff_name`   | varchar(100)   | YES  | NULL       | Staff member name |
| `login_time`   | datetime       | YES  | NULL       | Clock-in time |
| `logout_time`  | datetime       | YES  | NULL       | Clock-out time |
| `date`         | date           | YES  | NULL       | Attendance date |
| `hours_worked` | decimal(5,2)   | YES  | NULL       | Computed working hours |
| `status`       | varchar(20)    | YES  | NULL       | Attendance status (present, late, absent, etc.) |
| `notes`        | text           | YES  | NULL       | Additional notes |
| `created_at`   | timestamp      | YES  | CURRENT_TIMESTAMP | Record creation time |

---

### `card_wallet`

**Purpose:** Snapshot of member card/wallet data — balance in minutes, tier, and last top-up info. Denormalised for quick lookups.

| Column        | Type           | Null | Key | Default    | Description |
|---------------|----------------|------|-----|------------|-------------|
| `id`          | int            | NO   | PRI | auto-inc   | Primary key |
| `member_id`   | varchar(50)    | YES  | UNI | NULL       | Unique member identifier |
| `member_name` | varchar(100)   | YES  |     | NULL       | Member display name |
| `phone`       | varchar(20)    | YES  |     | NULL       | Contact phone number |
| `balance_mins`| decimal(10,2)  | YES  |     | NULL       | Available play minutes |
| `tier`        | varchar(20)    | YES  |     | NULL       | Membership tier/level |
| `total_spend` | decimal(10,2)  | YES  |     | NULL       | Total spend by member |
| `last_topup`  | datetime       | YES  |     | NULL       | Most recent top-up date |
| `last_updated`| timestamp      | YES  |     | CURRENT_TIMESTAMP | Last row update |

---

### `console_booking`

**Purpose:** Records game console bookings made by members, including time slots, staff who processed the booking, and status.

| Column            | Type           | Null | Default    | Description |
|-------------------|----------------|------|------------|-------------|
| `id`              | int            | NO   | auto-inc   | Primary key |
| `console_id`      | varchar(20)    | YES  | NULL       | Console identifier (e.g., PS4-01) |
| `member_id`       | varchar(50)    | YES  | NULL       | Member who booked |
| `booking_date`    | date           | YES  | NULL       | Date of booking |
| `start_time`      | datetime       | YES  | NULL       | Session start time |
| `end_time`        | datetime       | YES  | NULL       | Session end time |
| `status`          | varchar(20)    | YES  | NULL       | Booking status (active, completed, cancelled) |
| `staff_name`      | varchar(100)   | YES  | NULL       | Staff who processed the booking |
| `notes`           | text           | YES  | NULL       | Additional notes |
| `created_at`      | timestamp      | YES  | CURRENT_TIMESTAMP | Record creation time |
| `telegram_chat_id`| varchar(50)    | YES  | ''         | Telegram chat ID for notifications |
| `duration_mins`   | int            | YES  | 0          | Booking duration in minutes |
| `phone`           | varchar(50)    | YES  | ''         | Contact phone |
| `game_name`       | varchar(200)   | YES  | ''         | Game selected for the session |

---

### `console_games`

**Purpose:** Maps games to consoles — which games are installed/available on each console, with genre and slot position.

| Column         | Type           | Null | Key | Default    | Description |
|----------------|----------------|------|-----|------------|-------------|
| `id`           | int            | NO   | PRI | auto-inc   | Primary key |
| `console_id`   | varchar(20)    | NO   | MUL | NULL       | Console identifier |
| `console_name` | varchar(100)   | NO   |     | NULL       | Console display name |
| `game_id`      | varchar(50)    | NO   | MUL | NULL       | Game identifier |
| `game_title`   | varchar(200)   | NO   |     | NULL       | Game title |
| `genre`        | varchar(100)   | YES  |     | NULL       | Game genre |
| `status`       | varchar(20)    | YES  | MUL | active     | Game status (active, inactive) |
| `slot_position`| int            | YES  |     | 0          | Display order slot |
| `created_at`   | timestamp      | YES  |     | CURRENT_TIMESTAMP | Record creation time |
| `updated_at`   | timestamp      | YES  |     | CURRENT_TIMESTAMP | Auto-updated on change |

**Indexes:** `idx_console_id`, `idx_game_id`, `idx_status`

---

### `console_status`

**Purpose:** Real-time status of each gaming console — currently in use, type, current game/member, and last activity time.

| Column           | Type           | Null | Default    | Description |
|------------------|----------------|------|------------|-------------|
| `console_id`     | varchar(20)    | NO   | NULL       | Console identifier (PK) |
| `status`         | varchar(50)    | YES  | NULL       | Current status (idle, in_use, offline) |
| `console_type`   | varchar(50)    | YES  | ''         | Console type (PS4, PS5, etc.) |
| `current_game`   | text           | YES  | NULL       | Game currently being played |
| `current_member` | varchar(100)   | YES  | NULL       | Member currently using the console |
| `start_time`     | datetime       | YES  | NULL       | When current session started |
| `last_updated`   | datetime       | YES  | CURRENT_TIMESTAMP | When status last changed |

---

### `finance_advances`

**Purpose:** Tracks cash advances given to members (loans against future play or purchases).

| Column        | Type           | Null | Default    | Description |
|---------------|----------------|------|------------|-------------|
| `id`          | int            | NO   | auto-inc   | Primary key |
| `member_id`   | varchar(50)    | YES  | NULL       | Member who received the advance |
| `amount`      | decimal(15,2)  | YES  | NULL       | Advance amount |
| `advance_date`| date           | YES  | NULL       | Date advance was given |
| `settle_date` | date           | YES  | NULL       | Date advance was/will be settled |
| `status`      | varchar(20)    | YES  | pending    | Status (pending, settled, cancelled) |
| `notes`       | text           | YES  | NULL       | Additional notes |
| `created_at`  | timestamp      | YES  | CURRENT_TIMESTAMP | Record creation time |

---

### `finance_assets`

**Purpose:** Records business asset purchases (e.g., equipment, furniture, consoles) for financial tracking.

| Column          | Type           | Null | Default    | Description |
|-----------------|----------------|------|------------|-------------|
| `id`            | int            | NO   | auto-inc   | Primary key |
| `name`          | varchar(200)   | YES  | NULL       | Asset name/description |
| `purchase_date` | date           | YES  | NULL       | Date asset was purchased |
| `amount`        | decimal(15,2)  | YES  | NULL       | Purchase cost |
| `notes`         | text           | YES  | NULL       | Additional notes |
| `created_at`    | timestamp      | YES  | CURRENT_TIMESTAMP | Record creation time |

---

### `finance_opex_log`

**Purpose:** Records operating expenses (daily/monthly operational costs) categorised by type.

| Column        | Type           | Null | Default    | Description |
|---------------|----------------|------|------------|-------------|
| `id`          | int            | NO   | auto-inc   | Primary key |
| `date`        | date           | YES  | NULL       | Expense date |
| `category`    | varchar(100)   | YES  | NULL       | Expense category (utilities, rent, supplies, etc.) |
| `amount`      | decimal(15,2)  | YES  | NULL       | Expense amount |
| `description` | text           | YES  | NULL       | Detailed description of the expense |
| `created_at`  | timestamp      | YES  | CURRENT_TIMESTAMP | Record creation time |

---

### `finance_payables`

**Purpose:** Tracks money the business owes to suppliers, vendors, or other payees.

| Column      | Type           | Null | Default    | Description |
|-------------|----------------|------|------------|-------------|
| `id`        | int            | NO   | auto-inc   | Primary key |
| `payee`     | varchar(200)   | YES  | NULL       | Recipient/payee name |
| `amount`    | decimal(15,2)  | YES  | NULL       | Amount payable |
| `due_date`  | date           | YES  | NULL       | Payment due date |
| `status`    | varchar(20)    | YES  | pending    | Status (pending, paid, overdue) |
| `created_at`| timestamp      | YES  | CURRENT_TIMESTAMP | Record creation time |

---

### `finance_prepaid`

**Purpose:** Tracks prepaid expenses — payments made in advance for services or goods not yet received.

| Column        | Type           | Null | Default    | Description |
|---------------|----------------|------|------------|-------------|
| `id`          | int            | NO   | auto-inc   | Primary key |
| `description` | varchar(200)   | YES  | NULL       | Description of the prepaid item |
| `amount`      | decimal(15,2)  | YES  | NULL       | Prepaid amount |
| `settle_date` | date           | YES  | NULL       | Expected settlement/consumption date |
| `status`      | varchar(20)    | YES  | pending    | Status (pending, settled) |
| `created_at`  | timestamp      | YES  | CURRENT_TIMESTAMP | Record creation time |

---

### `finance_receivables`

**Purpose:** Tracks money owed to the business by customers, members, or other payers.

| Column      | Type           | Null | Default    | Description |
|-------------|----------------|------|------------|-------------|
| `id`        | int            | NO   | auto-inc   | Primary key |
| `payer`     | varchar(200)   | YES  | NULL       | Payer name |
| `amount`    | decimal(15,2)  | YES  | NULL       | Amount receivable |
| `due_date`  | date           | YES  | NULL       | Payment due date |
| `status`    | varchar(20)    | YES  | pending    | Status (pending, collected, overdue) |
| `created_at`| timestamp      | YES  | CURRENT_TIMESTAMP | Record creation time |

---

### `games_library`

**Purpose:** Master catalogue of all games available at the venue, including genre, single/multiplayer info, and disc count.

| Column        | Type           | Null | Default    | Description |
|---------------|----------------|------|------------|-------------|
| `game_title`  | varchar(200)   | NO   | NULL       | Game title (PK) |
| `genre`       | varchar(100)   | YES  | NULL       | Game genre |
| `solo_multi`  | varchar(50)    | YES  | ''         | Solo, multiplayer, or both |
| `final_status`| text           | YES  | NULL       | Game condition/status |
| `disc_count`  | int            | YES  | 0          | Number of discs/copies |
| `last_updated`| datetime       | YES  | CURRENT_TIMESTAMP | Last update time |

---

### `inventory`

**Purpose:** Tracks physical inventory items — food/drink/supplies stock levels, unit prices, and reorder thresholds.

| Column         | Type           | Null | Default    | Description |
|----------------|----------------|------|------------|-------------|
| `id`           | int            | NO   | auto-inc   | Primary key |
| `item_name`    | varchar(200)   | YES  | NULL       | Item name |
| `category`     | varchar(100)   | YES  | NULL       | Item category (food, drinks, supplies) |
| `quantity`     | int            | YES  | NULL       | Current stock quantity |
| `unit_price`   | decimal(10,2)  | YES  | NULL       | Selling price per unit |
| `reorder_level`| int            | YES  | NULL       | Low-stock threshold for reorder alerts |
| `last_updated` | timestamp      | YES  | CURRENT_TIMESTAMP | Last stock update |

---

### `member_wallets`

**Purpose:** Comprehensive member wallet record — play minutes, spend amounts, tier, referral info, and lifetime metrics. Central table for member financial data.

| Column              | Type           | Null | Default    | Description |
|---------------------|----------------|------|------------|-------------|
| `member_id`         | varchar(50)    | NO   | NULL       | Unique member identifier (PK) |
| `balance_mins`      | int            | YES  | 0          | Current available play minutes |
| `total_bought_mins` | int            | YES  | 0          | Total minutes purchased historically |
| `total_used_mins`   | int            | YES  | 0          | Total minutes used historically |
| `member_name`       | varchar(200)   | YES  | NULL       | Member name |
| `phone`             | varchar(50)    | YES  | NULL       | Contact phone |
| `effective_rate`    | decimal(10,2)  | YES  | 1.00       | Effective per-minute rate |
| `tier`              | varchar(50)    | YES  | NULL       | Membership tier/level |
| `total_spend`       | decimal(15,2)  | YES  | 0.00       | Total spend (may include adjustments) |
| `last_updated`      | datetime       | YES  | CURRENT_TIMESTAMP | Last row update |
| `lifetime_spend`    | decimal(12,2)  | YES  | 0.00       | Lifetime total spend |
| `ranking_net_spend` | decimal(12,2)  | YES  | 0.00       | Net spend used for ranking calculations |
| `reg_staff`         | varchar(100)   | YES  | NULL       | Staff who registered this member |
| `referral_code`     | varchar(50)    | YES  | NULL       | Member's unique referral code |
| `join_date`         | date           | YES  | NULL       | Membership registration date |

---

### `members`

**Purpose:** Core member registration table. Stores basic identity and current minute balance.

| Column            | Type           | Null | Key | Default    | Description |
|-------------------|----------------|------|-----|------------|-------------|
| `id`              | int            | NO   | PRI | auto-inc   | Auto-increment primary key |
| `member_id`       | varchar(50)    | NO   | UNI | NULL       | Unique member identifier |
| `name`            | varchar(255)   | YES  |     | NULL       | Member display name |
| `phone`           | varchar(50)    | YES  |     | NULL       | Phone number |
| `balance_minutes` | decimal(10,2)  | YES  |     | 0.00       | Available play minutes |
| `created_at`      | timestamp      | YES  |     | CURRENT_TIMESTAMP | Registration time |
| `updated_at`      | timestamp      | YES  |     | CURRENT_TIMESTAMP | Last update time |

---

### `promotions`

**Purpose:** Defines promotional campaigns — discount types, values, validity periods, and status.

| Column          | Type           | Null | Default    | Description |
|-----------------|----------------|------|------------|-------------|
| `id`            | int            | NO   | auto-inc   | Primary key |
| `promo_name`    | varchar(100)   | YES  | NULL       | Promotion display name |
| `discount_type` | varchar(50)    | YES  | NULL       | Discount type (percentage, fixed amount, etc.) |
| `discount_value`| decimal(10,2)  | YES  | NULL       | Discount amount/value |
| `start_date`    | date           | YES  | NULL       | Promotion start date |
| `end_date`      | date           | YES  | NULL       | Promotion end date |
| `status`        | varchar(20)    | YES  | NULL       | Status (active, expired, disabled) |
| `notes`         | text           | YES  | NULL       | Additional notes |
| `created_at`    | timestamp      | YES  | CURRENT_TIMESTAMP | Record creation time |

---

### `promotions_log`

**Purpose:** Audit log tracking every promotion/discount redemption by members, including voucher details and applied amounts.

| Column          | Type           | Null | Default    | Description |
|-----------------|----------------|------|------------|-------------|
| `id`            | int            | NO   | auto-inc   | Primary key |
| `voucher_no`    | varchar(50)    | YES  | NULL       | Voucher/receipt number |
| `promo_id`      | varchar(50)    | YES  | NULL       | Promotion identifier |
| `promo_title`   | varchar(200)   | YES  | NULL       | Promotion title/name |
| `member_id`     | varchar(50)    | YES  | NULL       | Member who redeemed |
| `console_id`    | varchar(20)    | YES  | NULL       | Console used (if applicable) |
| `gross_total`   | decimal(10,2)  | YES  | 0.00       | Total before discount |
| `discount_amt`  | decimal(10,2)  | YES  | 0.00       | Discount amount applied |
| `net_total`     | decimal(10,2)  | YES  | 0.00       | Total after discount |
| `staff_name`    | varchar(100)   | YES  | NULL       | Staff who processed the redemption |
| `promo_date`    | date           | YES  | NULL       | Date of redemption |
| `created_at`    | timestamp      | YES  | CURRENT_TIMESTAMP | Record creation time |

---

### `receipts`

**Purpose:** Payment receipts issued to members for purchases, top-ups, and services.

| Column          | Type           | Null | Key | Default    | Description |
|-----------------|----------------|------|-----|------------|-------------|
| `id`            | int            | NO   | PRI | auto-inc   | Primary key |
| `receipt_no`    | varchar(50)    | YES  | UNI | NULL       | Unique receipt number |
| `member_id`     | varchar(50)    | YES  |     | NULL       | Member identifier |
| `amount`        | decimal(10,2)  | YES  |     | NULL       | Total amount |
| `payment_method`| varchar(50)    | YES  |     | NULL       | Payment method (cash, card, transfer) |
| `items`         | text           | YES  |     | NULL       | Itemised list (JSON or text) |
| `receipt_date`  | datetime       | YES  |     | NULL       | Date/time of receipt |
| `staff_name`    | varchar(100)   | YES  |     | NULL       | Staff who issued the receipt |
| `created_at`    | timestamp      | YES  |     | CURRENT_TIMESTAMP | Record creation time |

---

### `referral_log`

**Purpose:** Tracks member referrals — who referred whom, which referral code was used, and reward amounts granted.

| Column           | Type           | Null | Key | Default       | Description |
|------------------|----------------|------|-----|---------------|-------------|
| `id`             | int            | NO   | PRI | auto-inc      | Primary key |
| `member_id`      | varchar(20)    | NO   | MUL | NULL          | Referee (new member who was referred) |
| `referrer_id`    | varchar(20)    | NO   | MUL | NULL          | Referrer (existing member who referred) |
| `referral_code`  | varchar(50)    | YES  | MUL | NULL          | Referral code used |
| `referred_at`    | timestamp      | YES  |     | CURRENT_TIMESTAMP | When the referral occurred |
| `reward_granted` | int            | YES  |     | 0             | Whether reward was granted (boolean: 0/1) |
| `reward_amount`  | decimal(10,2)  | YES  |     | 0.00          | Reward amount granted |
| `source`         | varchar(50)    | YES  |     | customer_bot  | Source system (customer_bot, sale_bot, etc.) |
| `notes`          | text           | YES  |     | NULL          | Additional notes |

**Indexes:** `idx_member_id`, `idx_referrer_id`, `idx_referral_code`

---

### `salary_advance`

**Purpose:** Records salary advances paid to staff members before payday.

| Column             | Type           | Null | Default    | Description |
|--------------------|----------------|------|------------|-------------|
| `id`               | int            | NO   | auto-inc   | Primary key |
| `staff_name`       | varchar(100)   | YES  | NULL       | Staff member name |
| `amount`           | decimal(10,2)  | YES  | NULL       | Advance amount |
| `advance_date`     | date           | YES  | NULL       | Date advance was given |
| `repayment_status` | varchar(20)    | YES  | NULL       | Repayment status (pending, repaid, partial) |
| `notes`            | text           | YES  | NULL       | Additional notes |
| `created_at`       | timestamp      | YES  | CURRENT_TIMESTAMP | Record creation time |

---

### `salary_payroll`

**Purpose:** Staff payroll processing records — base salary, bonuses, deductions, and net pay per pay period.

| Column        | Type           | Null | Default    | Description |
|---------------|----------------|------|------------|-------------|
| `id`          | int            | NO   | auto-inc   | Primary key |
| `staff_name`  | varchar(100)   | YES  | NULL       | Staff member name |
| `base_salary` | decimal(10,2)  | YES  | NULL       | Base salary amount |
| `bonus`       | decimal(10,2)  | YES  | NULL       | Bonus amount |
| `deductions`  | decimal(10,2)  | YES  | NULL       | Deductions amount |
| `net_salary`  | decimal(10,2)  | YES  | NULL       | Net salary (base + bonus - deductions) |
| `pay_period`  | varchar(50)    | YES  | NULL       | Pay period identifier (e.g., "2026-05") |
| `pay_date`    | date           | YES  | NULL       | Payment date |
| `status`      | varchar(20)    | YES  | NULL       | Payment status (paid, pending) |
| `notes`       | text           | YES  | NULL       | Additional notes |
| `created_at`  | timestamp      | YES  | CURRENT_TIMESTAMP | Record creation time |

---

### `sales_daily`

**Purpose:** Daily sales transactions with voucher tracking — records each sale with console/member details, pricing breakdown, and payment method.

| Column          | Type           | Null | Default    | Description |
|-----------------|----------------|------|------------|-------------|
| `id`            | int            | NO   | auto-inc   | Primary key |
| `voucher_no`    | varchar(50)    | YES  | NULL       | Unique voucher/receipt number |
| `sale_date`     | date           | YES  | NULL       | Date of sale |
| `console_id`    | varchar(20)    | YES  | NULL       | Console used |
| `member_id`     | varchar(50)    | YES  | NULL       | Member who made the purchase |
| `amount`        | decimal(10,2)  | YES  | NULL       | Total charged amount |
| `gross`         | decimal(10,2)  | YES  | 0.00       | Gross amount before discount |
| `discount`      | decimal(10,2)  | YES  | 0.00       | Discount applied |
| `net`           | decimal(10,2)  | YES  | 0.00       | Net amount after discount |
| `staff_name`    | varchar(100)   | YES  | NULL       | Staff who processed the sale |
| `payment_method`| varchar(50)    | YES  | NULL       | Payment method used |
| `notes`         | text           | YES  | NULL       | Additional notes |
| `created_at`    | timestamp      | YES  | CURRENT_TIMESTAMP | Record creation time |
| `updated_at`    | timestamp      | YES  | CURRENT_TIMESTAMP | Last update time |

---

### `settings`

**Purpose:** Legacy key-value application settings store. Superseded by `settings_config` for new configuration.

| Column          | Type           | Null | Key | Default    | Description |
|-----------------|----------------|------|-----|------------|-------------|
| `id`            | int            | NO   | PRI | auto-inc   | Primary key |
| `setting_key`   | varchar(100)   | YES  | UNI | NULL       | Unique setting key name |
| `setting_value` | text           | YES  |     | NULL       | Setting value (text) |
| `updated_at`    | timestamp      | YES  |     | CURRENT_TIMESTAMP | Last update time |

---

### `settings_config`

**Purpose:** Typed application configuration store with schema enforcement — supports string, int, float, JSON, and boolean types, categorised by module.

| Column          | Type                                    | Null | Key | Default    | Description |
|-----------------|-----------------------------------------|------|-----|------------|-------------|
| `id`            | int                                     | NO   | PRI | auto-inc   | Primary key |
| `config_key`    | varchar(100)                            | NO   | UNI | NULL       | Unique configuration key |
| `config_value`  | text                                    | NO   |     | NULL       | Configuration value |
| `config_type`   | enum('string','int','float','json','bool') | YES |   | string     | Data type for validation/parsing |
| `category`      | varchar(50)                             | YES  | MUL | general    | Config category/group |
| `description`   | varchar(255)                            | YES  |     | ''         | Human-readable description |
| `updated_at`    | timestamp                               | YES  |     | CURRENT_TIMESTAMP | Last update time |

**Indexes:** `config_key` (UNIQUE), `idx_key`, `idx_category`

---

### `staff_records`

**Purpose:** Staff member registry — personal details, salary, role, and active status.

| Column        | Type           | Null | Key | Default    | Description |
|---------------|----------------|------|-----|------------|-------------|
| `staff_id`    | int            | NO   | PRI | auto-inc   | Primary key |
| `staff_name`  | varchar(200)   | NO   | UNI | NULL       | Unique staff display name |
| `base_salary` | decimal(12,2)  | YES  |     | 0.00       | Base monthly salary |
| `role`        | varchar(100)   | YES  |     | NULL       | Job role/title |
| `is_active`   | tinyint(1)     | YES  |     | 1          | Active status (1=active, 0=inactive) |
| `last_updated`| datetime       | YES  |     | CURRENT_TIMESTAMP | Last update time |

---

### `staff_records_bak`

**Purpose:** Legacy backup table for `staff_records`. Same structure but with manual `staff_id` assignment.

| Column        | Type           | Null | Key | Default    | Description |
|---------------|----------------|------|-----|------------|-------------|
| `staff_id`    | int            | NO   | UNI | 0          | Staff ID (manually assigned) |
| `staff_name`  | varchar(200)   | NO   |     | NULL       | Staff display name |
| `base_salary` | decimal(12,2)  | YES  |     | 0.00       | Base salary |
| `role`        | varchar(100)   | YES  |     | NULL       | Job role |
| `is_active`   | tinyint(1)     | YES  |     | 1          | Active status |
| `last_updated`| datetime       | YES  |     | CURRENT_TIMESTAMP | Last update time |

---

### `stock_in`

**Purpose:** Records inventory stock-in transactions — batch tracking of items added to inventory with unit cost and total cost.

| Column       | Type           | Null | Key | Default    | Description |
|--------------|----------------|------|-----|------------|-------------|
| `id`         | int            | NO   | PRI | auto-inc   | Primary key |
| `batch_id`   | varchar(50)    | NO   | UNI | NULL       | Unique batch identifier |
| `item_name`  | varchar(200)   | NO   |     | NULL       | Item name |
| `quantity`   | int            | NO   |     | 0          | Quantity received |
| `unit_cost`  | decimal(10,2)  | NO   |     | 0.00       | Cost per unit |
| `total_cost` | decimal(12,2)  | YES  |     | *generated* | Computed: `quantity * unit_cost` (STORED GENERATED) |
| `source`     | varchar(100)   | YES  |     | ''         | Supplier/source |
| `receipt_no` | varchar(100)   | YES  |     | ''         | Supplier receipt/reference number |
| `created_at` | timestamp      | YES  |     | CURRENT_TIMESTAMP | Record creation time |

---

### `stock_out`

**Purpose:** Records inventory stock-out transactions — items sold or used, with sale price and staff attribution.

| Column       | Type           | Null | Default    | Description |
|--------------|----------------|------|------------|-------------|
| `id`         | int            | NO   | auto-inc   | Primary key |
| `item_name`  | varchar(200)   | YES  | NULL       | Item name |
| `quantity`   | int            | YES  | NULL       | Quantity sold/used |
| `unit_price` | decimal(10,2)  | YES  | NULL       | Selling price per unit |
| `total`      | decimal(10,2)  | YES  | NULL       | Total sale amount |
| `sale_date`  | datetime       | YES  | NULL       | Date/time of sale |
| `staff_name` | varchar(100)   | YES  | NULL       | Staff who processed the sale |
| `notes`      | text           | YES  | NULL       | Additional notes |
| `created_at` | timestamp      | YES  | CURRENT_TIMESTAMP | Record creation time |

---

### `sync_status`

**Purpose:** Tracks Google Sheets sync operations — which sheets were synced, when, and how many rows.

| Column         | Type           | Null | Key | Default    | Description |
|----------------|----------------|------|-----|------------|-------------|
| `id`           | int            | NO   | PRI | auto-inc   | Primary key |
| `sheet_name`   | varchar(100)   | NO   | UNI | NULL       | Google Sheets sheet name |
| `last_sync_at` | datetime       | NO   |     | NULL       | Last sync timestamp |
| `rows_synced`  | int            | YES  |     | 0          | Number of rows synced |
| `status`       | varchar(20)    | YES  |     | pending    | Sync status (pending, syncing, completed, error) |
| `created_at`   | datetime       | YES  |     | CURRENT_TIMESTAMP | Row creation time |
| `updated_at`   | datetime       | YES  |     | CURRENT_TIMESTAMP | Last update time |

---

### `topup_log`

**Purpose:** Audit log of member top-up transactions — amount paid, minutes added, balance before/after, and staff who processed.

| Column              | Type           | Null | Default    | Description |
|---------------------|----------------|------|------------|-------------|
| `id`                | int            | NO   | auto-inc   | Primary key |
| `member_id`         | varchar(50)    | YES  | NULL       | Member who topped up |
| `amount`            | decimal(10,2)  | YES  | NULL       | Monetary amount paid |
| `mins_added`        | int            | YES  | 0          | Play minutes added |
| `topup_date`        | datetime       | YES  | NULL       | Date/time of top-up |
| `staff_name`        | varchar(100)   | YES  | NULL       | Staff who processed |
| `payment_method`    | varchar(50)    | YES  | NULL       | Payment method used |
| `balance_before`    | decimal(10,2)  | YES  | NULL       | Money balance before top-up |
| `balance_after`     | decimal(10,2)  | YES  | NULL       | Money balance after top-up |
| `balance_mins_before`| int           | YES  | 0          | Minute balance before top-up |
| `balance_mins_after` | int           | YES  | 0          | Minute balance after top-up |
| `notes`             | text           | YES  | NULL       | Additional notes |
| `created_at`        | timestamp      | YES  | CURRENT_TIMESTAMP | Record creation time |

---

## Key Relationships & Foreign Key Notes

The database uses **logical relationships** rather than formal foreign key constraints. The following relationships exist across tables:

### Core Member Relationships

| Source Table          | Column        | References              | Description |
|-----------------------|---------------|-------------------------|-------------|
| `members`             | `member_id`   | — (UNIQUE)              | Central member identity |
| `member_wallets`      | `member_id`   | `members.member_id`     | Wallet details per member |
| `card_wallet`         | `member_id`   | `members.member_id`     | Snapshot wallet data (denormalised) |
| `console_booking`     | `member_id`   | `members.member_id`     | Bookings linked to member |
| `topup_log`           | `member_id`   | `members.member_id`     | Top-up transactions per member |
| `sales_daily`         | `member_id`   | `members.member_id`     | Sales transactions per member |
| `receipts`            | `member_id`   | `members.member_id`     | Receipts per member |
| `finance_advances`    | `member_id`   | `members.member_id`     | Cash advances per member |
| `referral_log`        | `member_id`   | `members.member_id`     | Referral records (referee) |
| `referral_log`        | `referrer_id` | `members.member_id`     | Referral records (referrer) |
| `promotions_log`      | `member_id`   | `members.member_id`     | Promotion redemptions per member |

### Console Relationships

| Source Table          | Column        | References                | Description |
|-----------------------|---------------|---------------------------|-------------|
| `console_status`      | `console_id`  | — (PK)                    | Central console identity |
| `console_games`       | `console_id`  | `console_status.console_id` | Games installed on each console |
| `console_booking`     | `console_id`  | `console_status.console_id` | Bookings per console |
| `sales_daily`         | `console_id`  | `console_status.console_id` | Sales attributed to a console |

### Staff Relationships

| Source Table          | Column        | References                    | Description |
|-----------------------|---------------|-------------------------------|-------------|
| `staff_records`       | `staff_name`  | — (UNIQUE)                    | Central staff identity |
| `attendance_log`      | `staff_name`  | `staff_records.staff_name`    | Attendance records |
| `salary_payroll`      | `staff_name`  | `staff_records.staff_name`    | Payroll records |
| `salary_advance`      | `staff_name`  | `staff_records.staff_name`    | Salary advances |

### Inventory Relationships

| Source Table          | Column        | References      | Description |
|-----------------------|---------------|-----------------|-------------|
| `inventory`           | `item_name`   | —               | Central inventory item identity |
| `stock_in`            | `item_name`   | `inventory.item_name` | Stock-in records per item |
| `stock_out`           | `item_name`   | `inventory.item_name` | Stock-out records per item |

### Promotion Relationships

| Source Table          | Column        | References                  | Description |
|-----------------------|---------------|-----------------------------|-------------|
| `promotions`          | `id`          | — (PK)                      | Central promotion definition |
| `promotions_log`      | `promo_id`    | `promotions.id`             | Promotion usage log |

### Settings

| Source Table          | Column        | References      | Description |
|-----------------------|---------------|-----------------|-------------|
| `settings`            | `setting_key` | — (UNIQUE)      | Legacy key-value settings |
| `settings_config`     | `config_key`  | — (UNIQUE)      | New typed configuration store |

---

## Engine & Collation Notes

- **Engine:** All tables use InnoDB for ACID compliance and foreign key support.
- **Default charset/collation:** `utf8mb4` / `utf8mb4_0900_ai_ci` (MySQL 8.0 default)
  - Exception: `console_games`, `referral_log` use `utf8mb4_unicode_ci`
- **Generated column:** `stock_in.total_cost` is a **STORED GENERATED** column (`quantity * unit_cost`).
- **Auto-increment seeded values** vary per table (e.g., `console_booking` at 141, `member_wallets` variable).

---

## Table Count

**Total tables:** 31 (including 1 backup table: `staff_records_bak`)
