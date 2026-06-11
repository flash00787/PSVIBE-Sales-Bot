# API ENDPOINTS
> Auto-imported from `/root/psvibe-sales-bot/API_ENDPOINTS.md`

# PS VIBE API Endpoints

**Base URL:** `http://localhost:8000` / `https://ps-vibe.com`  
**Auth:** `X-API-Key` header or `?api_key=` query parameter  
**Response Format (success):** `{"success": true, "data": <value>}`  
**Response Format (error):** `{"success": false, "error": "<message>", "code": <http_status>}`  
**Last Updated:** 2026-06-02

---

## Route Map

| # | Method | Path | Tag | Purpose |
|---|--------|------|-----|---------|
| 1 | GET | `/api/health` | System | Health check |
| 2 | GET | `/api/fetch_console_status` | Console | Live console status with bookings overlay |
| 3 | GET | `/api/fetch_members` | Members | Sorted list of all member IDs |
| 4 | GET | `/api/fetch_member_data/{member_id}` | Members | Consolidated member data |
| 5 | GET | `/api/fetch_wallet_mins/{member_id}` | Members | Wallet balance in minutes (cached) |
| 6 | GET | `/api/fetch_balance_mins/{member_id}` | Members | Wallet balance in minutes (live read) |
| 7 | GET | `/api/fetch_member_tier/{member_id}` | Members | Member's current tier |
| 8 | GET | `/api/fetch_staff` | Staff | List of staff names |
| 9 | GET | `/api/fetch_staff_names` | Staff | Alias for fetch_staff |
| 10 | GET | `/api/fetch_food_prices` | Food | Food item → price dict |
| 11 | GET | `/api/fetch_food_costs` | Food | Food item → cost price dict |
| 12 | GET | `/api/fetch_games` | Games | Game library (cached 10min) |
| 13 | GET | `/api/fetch_game_library` | Games | Alias for fetch_games |
| 14 | GET | `/api/fetch_console_games` | Games | Console-game installation records (cached 5min) |
| 15 | GET | `/api/get_games_on_console/{console_id}` | Games | Games installed on a specific console |
| 16 | GET | `/api/get_consoles_with_game` | Games | Consoles that have a specific game |
| 17 | GET | `/api/fetch_base_rate` | Settings | Hourly base rate (Ks/hr) |
| 18 | GET | `/api/fetch_console_multiplier/{console_id}` | Settings | Console pricing multiplier |
| 19 | GET | `/api/fetch_new_member_defaults` | Settings | Default card price + base mins |
| 20 | GET | `/api/fetch_rank_thresholds` | Settings | Master/Immortal spend thresholds |
| 21 | GET | `/api/fetch_bonus_table` | Settings | Staff bonus table |
| 22 | GET | `/api/fetch_rank_table_display` | Settings | Formatted rank bonus string |
| 23 | GET | `/api/fetch_alltime_effective_rate` | Analytics | All-time average Ks/min |
| 24 | GET | `/api/fetch_member_effective_rate/{member_id}` | Members | Member's stored effective rate |
| 25 | GET | `/api/build_member_rate_dict` | Members | All member → rate dict |
| 26 | GET | `/api/fetch_base_salaries` | Staff | Staff base salaries |
| 27 | GET | `/api/fetch_attendance/{month_str}` | Attendance | Attendance for a month |
| 28 | GET | `/api/fetch_salary_advances/{month_str}` | Attendance | Salary advances for a month |
| 29 | GET | `/api/fetch_promotions_cached` | Promotions | Active promotions (placeholder) |
| 30 | GET | `/api/fetch_allowed_staff_ids` | Staff | Dynamic staff Telegram whitelist |
| 31 | GET | `/api/next_voucher` | Sales | Next voucher number |
| 32 | GET | `/api/next_member_id` | Members | Next auto-incremented member ID |
| 33 | GET | `/api/next_member_row_no` | Members | Next row number for Card_Wallet |
| 34 | GET | `/api/fetch_referral_code/{member_id}` | Members | Member's referral code |
| 35 | POST | `/api/create_booking` | Bookings | Create booking record |
| 36 | PUT | `/api/end_booking/{booking_id}` | Bookings | End (complete) a booking |
| 37 | PUT | `/api/cancel_booking/{booking_id}` | Bookings | Cancel a booking |
| 38 | POST | `/api/save_attendance` | Attendance | Save/update attendance record |
| 39 | POST | `/api/save_receipt_json` | Receipts | Log receipt data |
| 40 | POST | `/api/add_console_game` | Games | Add game installation record |
| 41 | DELETE | `/api/remove_console_game` | Games | Remove game installation record |
| 42 | PUT | `/api/set_game_disc_count` | Games | Update available disc count |
| 43 | PUT | `/api/update_game_library_install` | Games | Toggle install checkbox in Game_Library |
| 44 | PUT | `/api/update_member_effective_rate` | Members | Update member effective rate |
| 45 | POST | `/api/save_referral_code` | Members | Save referral code |
| 46 | POST | `/api/add_console_to_setting` | Console | Add console row to Setting |
| 47 | DELETE | `/api/remove_console_from_setting/{console_id}` | Console | Remove console from Setting |
| 48 | GET | `/api/sheets/config` | Meta | Full cached bot config |
| 49 | GET | `/api/mysql/members` | MySQL | All member IDs from MySQL |
| 50 | GET | `/api/mysql/member_data/{member_id}` | MySQL | Member data from MySQL |
| 51 | GET | `/api/mysql/console_status` | MySQL | Console status from MySQL |
| 52 | GET | `/api/mysql/games` | MySQL | Game library from MySQL |
| 53 | GET | `/api/mysql/console_games` | MySQL | Console-game installations from MySQL |
| 54 | GET | `/api/mysql/staff` | MySQL | Staff records from MySQL |
| 55 | POST | `/api/mysql/sync` | MySQL | Trigger sheets→MySQL sync |
| 56 | GET | `/api/mysql/sync_status` | MySQL | Check MySQL sync status |
| 57 | GET | `/api/mysql/health` | MySQL | MySQL connection health |
| 58 | GET | `/api/analytics/daily_sales` | Analytics | Daily sales KPIs |
| 59 | GET | `/api/analytics/topups` | Analytics | Top-up trends |
| 60 | GET | `/api/analytics/member_activity` | Analytics | Member activity stats |
| 61 | GET | `/api/analytics/console_usage` | Analytics | Console usage stats |
| 62 | GET | `/api/analytics/dashboard` | Analytics | Full BI dashboard summary |
| 63 | GET | `/api/analytics/weekly_trends` | Analytics | Weekly aggregated trends |
| 64 | GET | `/dashboard` | — | BI web dashboard (HTML) |
| 65 | GET | `/api/dashboard` | — | BI web dashboard alias (HTML) |
| 66 | GET | `/api/bookings/search` | Bookings | Search bookings by filters |
| 67 | GET | `/api/bookings/{booking_id}` | Bookings | Get single booking by ID |
| 68 | POST | `/api/bookings` | Bookings | Create booking (customer bot format) |
| 69 | POST | `/api/feedback/submit` | Feedback | Submit customer feedback |
| 70 | POST | `/api/sheets/log` | Logging | Log AI interaction |
| 71 | POST | `/api/bot-users/track` | Bot Users | Track bot user activity |

---

## Endpoint Details

---

### `GET /api/health`
**Purpose:** Health check endpoint. Verifies API server and Google Sheets connectivity. No auth required.  
**Auth required:** No  
**Parameters:** None  
**Response:**
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "version": "1.x.x",
    "sheets_connected": true,
    "timestamp": "2026-06-02T22:30:00+06:30"
  }
}
```

---

### `GET /api/fetch_console_status`
**Purpose:** Return list of all consoles with live status (Free/Active/Scheduled) from Console_Booking sheet. Overlays today's bookings onto console definitions from Setting sheet.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": [{"id": "PS5-1", "type": "PS5", "mult": 1.0, "status": "Free", "member": null, "start": null, "staff": null, "booking_id": null}, ...]}`  

---

### `GET /api/fetch_members`
**Purpose:** Return sorted list of all member IDs from Card_Wallet sheet.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": ["PSV_A_001", "PSV_A_002", ...]}`  

---

### `GET /api/fetch_member_data/{member_id}`
**Purpose:** Return consolidated member profile data (name, phone, email, rank, wallet minutes, net spend).  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| member_id | string | path | Yes | Member ID (e.g. `PSV_A_001`) |

**Response:** `{"success": true, "data": {"name": "John", "phone": "09...", "email": "", "net_spend": 50000, "rank_raw": "Master", "wallet_mins": 120}}`  

---

### `GET /api/fetch_wallet_mins/{member_id}`
**Purpose:** Fetch wallet balance in minutes from Card_Wallet (uses cached rows).  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| member_id | string | path | Yes | Member ID |

**Response:** `{"success": true, "data": 120}`  

---

### `GET /api/fetch_balance_mins/{member_id}`
**Purpose:** Fetch wallet balance in minutes (live read, bypasses cache).  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| member_id | string | path | Yes | Member ID |

**Response:** `{"success": true, "data": 120}`  

---

### `GET /api/fetch_member_tier/{member_id}`
**Purpose:** Fetch member's current tier from Card_Wallet column G. Defaults to "Warrior".  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| member_id | string | path | Yes | Member ID |

**Response:** `{"success": true, "data": "Master"}`  

---

### `GET /api/fetch_staff`
**Purpose:** Return list of staff names from Setting sheet column S.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": ["Alice", "Bob", ...]}`  

---

### `GET /api/fetch_staff_names`
**Purpose:** Alias for `fetch_staff`.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** Same as `fetch_staff`.  

---

### `GET /api/fetch_food_prices`
**Purpose:** Return dict of food item name → selling price from Setting (D-E columns).  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": {"Fried Rice": 3000, "Pizza": 5000, ...}}`  

---

### `GET /api/fetch_food_costs`
**Purpose:** Return dict of food item name → cost price from Setting (D, F columns).  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": {"Fried Rice": 2000, "Pizza": 3500, ...}}`  

---

### `GET /api/fetch_games`
**Purpose:** Return all games from Game_Library sheet (cached 10 min).  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": [{"row": 2, "title": "Spider-Man 2", "platform": "PS5", "genre": "Action", "status": "Available", "discs": "1"}, ...]}`  

---

### `GET /api/fetch_game_library`
**Purpose:** Alias for `fetch_games`.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** Same as `fetch_games`.  

---

### `GET /api/fetch_console_games`
**Purpose:** Return all console-game installation records (cached 5 min).  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": [{"row": 2, "console_id": "PS5-1", "game_title": "Spider-Man 2", "install_type": "Digital", "date": "6/1/2026", "notes": ""}, ...]}`  

---

### `GET /api/get_games_on_console/{console_id}`
**Purpose:** Return list of game titles installed on a specific console.  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| console_id | string | path | Yes | Console identifier (e.g. `PS5-1`) |

**Response:** `{"success": true, "data": ["Spider-Man 2", "Elden Ring", ...]}`  

---

### `GET /api/get_consoles_with_game`
**Purpose:** Return list of console IDs that have a specific game installed.  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| game_title | string | query | Yes | Game title (exact match, case-insensitive) |

**Response:** `{"success": true, "data": ["PS5-1", "PS5-2"]}`  

---

### `GET /api/fetch_base_rate`
**Purpose:** Fetch hourly base rate from Setting!B2 (Ks/hr).  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": 800}`  

---

### `GET /api/fetch_console_multiplier/{console_id}`
**Purpose:** Fetch pricing multiplier for a specific console from Setting column J.  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| console_id | string | path | Yes | Console identifier |

**Response:** `{"success": true, "data": 1.5}`  

---

### `GET /api/fetch_new_member_defaults`
**Purpose:** Fetch default card price and base minutes from Setting cells B20:B21.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": {"card_price": 1000, "base_mins": 60}}`  

---

### `GET /api/fetch_rank_thresholds`
**Purpose:** Fetch Master and Immortal spend thresholds from Setting!M3:M4.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": {"master_threshold": 30000, "immortal_threshold": 100000}}`  

---

### `GET /api/fetch_bonus_table`
**Purpose:** Fetch staff bonus structure from Setting!O2:R5.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": [{"threshold": 30000, "warrior_bonus": 0, "master_bonus": 500, "immortal_bonus": 1000}, ...]}`  

---

### `GET /api/fetch_rank_table_display`
**Purpose:** Fetch Setting!O1:R5 and return as a formatted string table for terminal/chat display.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": "Amount (Ks)     Warrior   Master   Immortal\n------------------------------------------------\n..."}`  

---

### `GET /api/fetch_alltime_effective_rate`
**Purpose:** Calculate all-time average Ks/min ratio across every TopUp_Log row.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": 14.5}`  

---

### `GET /api/fetch_member_effective_rate/{member_id}`
**Purpose:** Fetch a member's stored effective rate from Card_Wallet column L.  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| member_id | string | path | Yes | Member ID |

**Response:** `{"success": true, "data": 12.5}`  

---

### `GET /api/build_member_rate_dict`
**Purpose:** Build dict of member_id → stored effective rate from Card_Wallet.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": {"PSV_A_001": 12.5, "PSV_A_002": 14.0, ...}}`  

---

### `GET /api/fetch_base_salaries`
**Purpose:** Fetch staff base salaries from Setting!S:T columns.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": {"Alice": 150000, "Bob": 120000, ...}}`  

---

### `GET /api/fetch_attendance/{month_str}`
**Purpose:** Fetch attendance records for a given month from Attendance_Log.  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| month_str | string | path | Yes | Month identifier (e.g. `6/2026`) |

**Response:** `{"success": true, "data": {"Alice": {"leave_days": 0, "late_count": 1, "deduct_per_late": 500}, ...}}`  

---

### `GET /api/fetch_salary_advances/{month_str}`
**Purpose:** Return salary advance totals per staff member for the given month.  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| month_str | string | path | Yes | Month in `YYYY-MM` format (e.g. `2026-06`) |

**Response:** `{"success": true, "data": {"Alice": {"total": 50000, "cash": 30000, "kpay": 20000}, ...}}`  

---

### `GET /api/fetch_promotions_cached`
**Purpose:** Placeholder for active promotions.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": [], "message": "Promotions API not yet integrated"}`  

---

### `GET /api/fetch_allowed_staff_ids`
**Purpose:** Fetch dynamic staff Telegram ID whitelist from Setting!B30.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": [123456789, 987654321]}`  

---

### `GET /api/next_voucher`
**Purpose:** Generate next voucher number (V-001, V-002...) from Sales_Daily column B.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": "V-042"}`  

---

### `GET /api/next_member_id`
**Purpose:** Auto-increment member ID (PSV_A_003 → PSV_A_004).  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": "PSV_A_042"}`  

---

### `GET /api/next_member_row_no`
**Purpose:** Return next sequential row number for Card_Wallet column A.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": 142}`  

---

### `GET /api/fetch_referral_code/{member_id}`
**Purpose:** Fetch referral code for a member from Card_Wallet.  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| member_id | string | path | Yes | Member ID |

**Response:** `{"success": true, "data": "ABC123"}` (or `null` if none)  

---

### `POST /api/create_booking`
**Purpose:** Create a new console booking. Appends a row to Console_Booking and generates a BookingID.  
**Auth required:** Yes  
**Request Body (JSON):**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| console_id | string | Yes | Console identifier |
| member_id | string | Yes | Member ID |
| staff | string | No | Staff name who handled booking |
| notes | string | No | Additional notes |

**Response:** `{"success": true, "data": {"booking_id": "BK-20260602-PS51-1423"}}`  

---

### `PUT /api/end_booking/{booking_id}`
**Purpose:** Mark a booking as Done and fill end time.  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| booking_id | string | path | Yes | Booking ID (e.g. `BK-20260602-PS51-1423`) |

**Response:** `{"success": true, "data": {"booking_id": "BK-...", "status": "Done"}}`  

---

### `PUT /api/cancel_booking/{booking_id}`
**Purpose:** Cancel a booking (sets status to "Cancelled").  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| booking_id | string | path | Yes | Booking ID |

**Response:** `{"success": true, "data": {"booking_id": "BK-...", "status": "Cancelled"}}`  

---

### `POST /api/save_attendance`
**Purpose:** Save or update an attendance record for a staff member in Attendance_Log.  
**Auth required:** Yes  
**Request Body (JSON):**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| month_str | string | Yes | Month identifier (e.g. `6/2026`) |
| staff | string | Yes | Staff name |
| leave_days | int | No | Number of leave days (default 0) |
| late_count | int | No | Number of late arrivals (default 0) |
| deduct_per_late | int | No | Deduction amount per late (default 500) |

**Response:** `{"success": true, "data": {"staff": "Alice", "month": "6/2026"}}`  

---

### `POST /api/save_receipt_json`
**Purpose:** Log/receipt data for a voucher (stored locally, no sheet write).  
**Auth required:** Yes  
**Request Body (JSON):**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| voucher_id | string | No | Voucher identifier |
| data | object | No | Receipt data payload |

**Response:** `{"success": true, "data": {"voucher_id": "V-042"}}`  

---

### `POST /api/add_console_game`
**Purpose:** Add a game installation record to Console_Games sheet.  
**Auth required:** Yes  
**Request Body (JSON):**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| console_id | string | Yes | Console identifier |
| game_title | string | Yes | Game title |
| install_type | string | No | Digital / Disc |
| notes | string | No | Additional notes |

**Response:** `{"success": true, "data": {"console_id": "PS5-1", "game_title": "Spider-Man 2"}}`  

---

### `DELETE /api/remove_console_game`
**Purpose:** Remove a game installation record from Console_Games.  
**Auth required:** Yes  
**Request Body (JSON):**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| console_id | string | Yes | Console identifier |
| game_title | string | Yes | Game title |

**Response:** `{"success": true, "data": {"console_id": "PS5-1", "game_title": "Spider-Man 2"}}`  

---

### `PUT /api/set_game_disc_count`
**Purpose:** Update available disc count (column D) for a game row in Game_Library.  
**Auth required:** Yes  
**Request Body (JSON):**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| row_num | int | Yes | Row number in Game_Library |
| count | int | Yes | Available disc count |

**Response:** `{"success": true, "data": {"row_num": 5, "count": 2}}`  

---

### `PUT /api/update_game_library_install`
**Purpose:** Set or clear the installed checkbox for a (game_title, console_id) pair in Game_Library.  
**Auth required:** Yes  
**Request Body (JSON):**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| game_title | string | Yes | Game title |
| console_id | string | Yes | Console identifier |
| installed | bool | Yes | `true` to mark installed, `false` to clear |

**Response:** `{"success": true, "data": {"game": "Spider-Man 2", "console": "PS5-1", "installed": true}}`  

---

### `PUT /api/update_member_effective_rate`
**Purpose:** Update or insert a member's effective rate in Card_Wallet column L.  
**Auth required:** Yes  
**Request Body (JSON):**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| member_id | string | Yes | Member ID |
| rate | number | Yes | Effective rate (Ks/min) |

**Response:** `{"success": true, "data": {"member_id": "PSV_A_001", "rate": 12.5}}`  

---

### `POST /api/save_referral_code`
**Purpose:** Save a referral code for a member in Card_Wallet.  
**Auth required:** Yes  
**Request Body (JSON):**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| member_id | string | Yes | Member ID |
| code | string | Yes | Referral code |

**Response:** `{"success": true, "data": {"member_id": "PSV_A_001", "code": "ABC123"}}`  

---

### `POST /api/add_console_to_setting`
**Purpose:** Append a new console row to Setting!H:J.  
**Auth required:** Yes  
**Request Body (JSON):**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| console_id | string | Yes | New console identifier |
| ctype | string | No | Console type (PS5, Xbox, etc.) |
| multiplier | number | No | Price multiplier (default 1.0) |

**Response:** `{"success": true, "data": {"console_id": "PS5-3"}}`  

---

### `DELETE /api/remove_console_from_setting/{console_id}`
**Purpose:** Clear a console row from Setting!H:J (sets cells to empty, does not delete row).  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| console_id | string | path | Yes | Console identifier to remove |

**Response:** `{"success": true, "data": {"console_id": "PS5-3"}}`  

---

### `GET /api/sheets/config`
**Purpose:** Return cached bot configuration (base rate, thresholds, console multipliers, food prices/costs, bonus table). Used by sales-bot for local cache refresh.  
**Auth required:** Yes  
**Parameters:** None  
**Response:**
```json
{
  "success": true,
  "data": {
    "base_rate": 800,
    "master_threshold": 30000,
    "immortal_threshold": 100000,
    "new_member_card_price": 1000,
    "new_member_base_mins": 60,
    "console_multipliers": {"PS5-1": 1.0, "PS4-1": 0.8},
    "food_prices": {"Fried Rice": 3000},
    "food_costs": {"Fried Rice": 2000},
    "bonus_table": [[30000, 0, 500, 1000]]
  }
}
```

---

### `GET /api/mysql/members`
**Purpose:** Fetch all member IDs from MySQL (faster than gspread). Returns 503 if MySQL is unavailable.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": ["PSV_A_001", "PSV_A_002", ...]}`  

---

### `GET /api/mysql/member_data/{member_id}`
**Purpose:** Fetch member data from MySQL.  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| member_id | string | path | Yes | Member ID |

**Response:** `{"success": true, "data": {"member_id": "PSV_A_001", ...}}`  

---

### `GET /api/mysql/console_status`
**Purpose:** Fetch console status from MySQL.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": [{"console_id": "PS5-1", ...}]}`  

---

### `GET /api/mysql/games`
**Purpose:** Fetch game library from MySQL.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": [{"title": "Spider-Man 2", ...}]}`  

---

### `GET /api/mysql/console_games`
**Purpose:** Fetch console-game installations from MySQL.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": [{"console_id": "PS5-1", "game_title": "Spider-Man 2", ...}]}`  

---

### `GET /api/mysql/staff`
**Purpose:** Fetch staff records from MySQL.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": [{"name": "Alice", ...}]}`  

---

### `POST /api/mysql/sync`
**Purpose:** Trigger a one-time Google Sheets → MySQL sync.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": {"synced": true, "details": "..."}}`  

---

### `GET /api/mysql/sync_status`
**Purpose:** Check MySQL sync status (last sync time, rows synced).  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": {"last_sync": "2026-06-02T22:00:00", ...}}`  

---

### `GET /api/mysql/health`
**Purpose:** MySQL connection health check.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": {"mysql": true, "sync_running": true}}`  

---

### `GET /api/analytics/daily_sales`
**Purpose:** Return today's (or specified date's) sales KPIs from Sales_Daily.  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| date | string | query | No | Date in M/D/YYYY format (defaults to today) |

**Response:** `{"success": true, "data": {"total_sales_ks": 50000, "voucher_count": 12, "by_payment": {...}, ...}}`  

---

### `GET /api/analytics/topups`
**Purpose:** Return top-up trends: daily/weekly aggregates, all-time effective rate, top members.  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| days | int | query | No | Number of days to analyze (1–365, default 30) |

**Response:** `{"success": true, "data": {"total_topups": 50, "total_amount_ks": 500000, ...}}`  

---

### `GET /api/analytics/member_activity`
**Purpose:** Return member activity stats: total members, tier distribution, active today, wallet totals.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": {"total_members": 200, "active_today": 15, "tier_distribution": [...], ...}}`  

---

### `GET /api/analytics/console_usage`
**Purpose:** Return console usage stats: bookings per console, utilization rate, daily series.  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| days | int | query | No | Number of days to analyze (1–365, default 30) |

**Response:** `{"success": true, "data": {"total_bookings": 120, "avg_bookings_per_console_day": 2.5, ...}}`  

---

### `GET /api/analytics/dashboard`
**Purpose:** Return full BI dashboard summary with all KPIs in one response.  
**Auth required:** Yes  
**Parameters:** None  
**Response:** `{"success": true, "data": {"summary": {...}, "daily_sales": {...}, "member_activity": {...}, "console_usage_today": {...}, "topup_trends_7d": {...}, "generated_at": "..."}}`  

---

### `GET /api/analytics/weekly_trends`
**Purpose:** Return weekly aggregated trends: sales, top-ups, and console usage by week.  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| weeks | int | query | No | Number of weeks to analyze (1–52, default 4) |

**Response:** `{"success": true, "data": {"period_weeks": 4, "topup_weekly": [...], "console_daily": [...], ...}}`  

---

### `GET /dashboard` / `GET /api/dashboard`
**Purpose:** Serve the BI web dashboard as an HTML page. Uses embedded API key for client-side fetches. Not included in OpenAPI schema.  
**Auth required:** No (served as HTML)  
**Parameters:** None  
**Response:** Full HTML page (BI dashboard with KPIs, tables, bar charts, auto-refresh 60s).  

---

### `GET /api/bookings/search`
**Purpose:** Search bookings by telegram_chat_id, date, and/or status.  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| telegram_chat_id | string | query | No | Filter by Telegram chat ID |
| date | string | query | No | Filter by date (M/D/YYYY format) |
| status | string | query | No | Filter by status (Active, Done, Cancelled, Pending) |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "booking_id": "BK-...",
      "date": "6/2/2026",
      "console_id": "PS5-1",
      "member_id": "",
      "timeSlot": "14:00",
      "endTime": "",
      "status": "Pending",
      "staff": "",
      "notes": "{\"customerName\":\"...\",\"phone\":\"...\"}",
      "telegramChatId": "123456789",
      "consoleType": "PS5",
      "gameName": "",
      "durationMins": 60
    }
  ]
}
```

---

### `GET /api/bookings/{booking_id}`
**Purpose:** Get a single booking by its ID.  
**Auth required:** Yes  
**Parameters:**

| Name | Type | In | Required | Description |
|------|------|----|----------|-------------|
| booking_id | string | path | Yes | Booking ID |

**Response:** `{"success": true, "data": {"booking_id": "BK-...", "date": "6/2/2026", "console_id": "PS5-1", ...}}`  

---

### `POST /api/bookings`
**Purpose:** Create a booking from customer bot payload (supports notes JSON with customer info).  
**Auth required:** Yes  
**Request Body (JSON):**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| customerName | string | No | Customer name |
| phone | string | No | Phone number |
| timeSlot | string | No | Preferred time slot |
| consoleType | string | No | Console type requested |
| durationMins | int | No | Duration in minutes |
| gameName | string | No | Game preference |
| telegramChatId | string | No | Customer's Telegram chat ID |
| username | string | No | Customer's Telegram username |

**Response:** `{"success": true, "data": {"id": "BK-...", "status": "Pending"}}`  

---

### `POST /api/feedback/submit`
**Purpose:** Accept customer feedback (fire-and-forget, logs to server).  
**Auth required:** Yes  
**Request Body (JSON):**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| tg_id | string | No | Telegram user ID |
| username | string | No | Telegram username |
| booking_id | string | No | Associated booking ID |
| rating | int | No | Rating (1–5) |
| comment | string | No | Feedback comment |

**Response:** `{"success": true, "data": {"received": true}}`  

---

### `POST /api/sheets/log`
**Purpose:** Log an AI interaction row (fire-and-forget).  
**Auth required:** Yes  
**Request Body (JSON):**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| tg_id | string | No | Telegram user ID |
| username | string | No | Telegram username |
| user_name | string | No | Display name |
| query | string | No | User query (truncated to 300 chars) |
| response | string | No | AI response (truncated to 500 chars) |
| sentiment | string | No | Sentiment label (default "neutral") |

**Response:** `{"success": true, "data": {"logged": true}}`  

---

### `POST /api/bot-users/track`
**Purpose:** Track bot user activity (fire-and-forget).  
**Auth required:** Yes  
**Request Body (JSON):**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| tg_id | string | No | Telegram user ID |
| username | string | No | Telegram username |
| user_name | string | No | Display name |
| action | string | No | Action performed |

**Response:** `{"success": true, "data": {"tracked": true}}`  

---

## Authentication

All endpoints except `/api/health`, `/dashboard`, and `/api/dashboard` require API key authentication.

**Methods:**
1. **Query Parameter:** `?api_key=YOUR_API_KEY`
2. **HTTP Header:** `X-API-Key: YOUR_API_KEY`

The API key is configured server-side in `config.py` as `API_KEY`. If no key is configured, auth is bypassed.

On auth failure: `HTTP 401` with `{"detail": "Invalid or missing API key"}`.

---

## Common Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success — `{"success": true, "data": <value>}` |
| 401 | Invalid/missing API key |
| 404 | Resource not found (member, booking, game, console) |
| 500 | Internal server error — `{"success": false, "detail": "<error>"}` |
| 503 | MySQL not available (MySQL endpoints only) |

---

## Notes

- All mutation endpoints (POST, PUT, DELETE) invalidate the relevant gspread cache after writing.
- Date/time values are in Myanmar Time (MMT, UTC+6:30).
- The `ok()` wrapper always returns `{"success": true, "data": <value>}`. If an optional `message` field is present, it's added as `"message": <string>`.
- MySQL endpoints (prefix `/api/mysql/...`) fall back gracefully with 503 if MySQL is not configured.
- The BI dashboard HTML serves at both `/dashboard` and `/api/dashboard` with embedded API key auto-injected.

---
*Imported on 2026-06-11*