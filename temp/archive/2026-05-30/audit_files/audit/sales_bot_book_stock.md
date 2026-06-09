# PS VIBE Sales Bot — Booking / Console / Stock Flow Trace

> **VPS:** `5.223.81.16` | **Bot dir:** `/root/psvibe-sale-bot/` | **Date:** 2026-05-28
>
> Architecture: Telegram Bot (python-telegram-bot) → Google Sheets (gspread) + Replit API Proxy (urllib→`API_BASE_URL/api/...`)

---

## Master Sheet Map

All Google Sheets access goes through one workbook (`SHEET_ID` env var):

| Sheet Tab | Python Var | Columns |
|-----------|-----------|---------|
| `Sales_Daily` | `sales_sh` | Sales vouchers |
| `Setting` | `setting_sh` | Console config (H/I/J), food prices (D/E), staff whitelist (B30), base rate (B2), etc. |
| `Card_Wallet` | `member_sh` | Members (A:Q) |
| `Stock_Out` | `stock_sh` | Stock-out records (A:H) |
| `Stock_In` | `stock_in_sh` | Stock-in records (A:G) |
| `TopUp_Log` | `topup_sh` | Top-up log |
| `Inventory` | `inv_sh` | Inventory status |
| `Console_Booking` | `get_booking_sh()` | Bookings: BookingID, Date, ConsoleID, MemberID, StartTime, EndTime, Status, Staff, Notes |
| `Console_Games` | `get_console_games_sh()` | Installs: Console_ID, Game_Title, Install_Type, Date, Notes |
| `Game_Library` | `get_game_lib_sh()` | Games: No, Game Name, Status, Discs, C-01..T7, SD1, SD2, Free Consoles, Installed_On(U) |
| `Salary_Advance` | `get_salary_adv_sh()` | Salary advances |
| `Attendance` | `get_att_sh()` | Staff attendance |

### API Proxy Pattern

All state reads/writes go through two paths:
1. **Direct gspread** — `fetch_games()`, `fetch_console_status()`, `fetch_console_games()`, `fetch_members()`, etc. (cached: 30s-10min TTL)
2. **Replit API (`_replit_get/_replit_post`)** — `sheets/consoles`, `sheets/config`, `sheets/inventory`, `bookings`, `bookings?status=pending`, `bookings?status=confirmed`, `bookings?memberId=X`

```python
# API base: env.API_BASE_URL + env.API_KEY
_replit_get("sheets/consoles")    # → GET  $API_BASE_URL/api/sheets/consoles
_replit_get("bookings?status=pending")  # → GET  .../api/bookings?status=pending
_replit_post("bookings", payload)      # → POST .../api/bookings  (create booking)
```

### n8n Webhook Integration

```python
N8N_SESSION_WEBHOOK  = os.environ.get("N8N_SESSION_WEBHOOK", "")   # Session reminders
N8N_BOOKING_WEBHOOK  = os.environ.get("N8N_BOOKING_WEBHOOK", "")   # Booking reminders
```

---

## FLOW 1: Session Booking (Walk-in / Console Session Start)

**Entry points:** `BTN_START_SESSION` (Console Menu) or `BTN_CONSOLE_BOOK` (Main Menu)

### State Chain

```
BOOK_LINK (48) → BOOK_CONSOLE (49) → BOOK_MEMBER (50) → BOOK_DUP_WARN (67) → BOOK_GAME (68) → BOOK_MINS (69) → DONE
                                                                                     ↓ SSD_XFER_SSD (session shortcut)
```

### Detailed State Table

| # | State | Handler Function | Sheet Tab | API Calls |
|---|-------|-----------------|-----------|-----------|
| 1 | `BOOK_LINK` | `step_book_link()` in `booking.py:682` | — | `_replit_get("bookings")` — checks today's confirmed/arrived bookings |
| 2 | `BOOK_CONSOLE` | `step_book_console()` in `booking.py:768` | Console_Booking (via `fetch_console_status()`) | `fetch_console_status()` → Setting col H/I/J + Console_Booking Active rows |
| 3 | `BOOK_MEMBER` | `step_book_member()` in `booking.py:793` | Card_Wallet (via `fetch_members()`) | `fetch_members()` → Card_Wallet col B; `fetch_staff()` → Setting or cached |
| 3a | `BOOK_DUP_WARN` | `step_book_dup_warn()` in `booking.py:1061` | — | `fetch_console_status()` for duplicate-session check; no write |
| 4 | `BOOK_GAME` | `step_book_game()` in `booking.py:915` | Console_Games | `get_games_on_console(cid)`; may redirect to `SSD_XFER_SSD` |
| 5 | `BOOK_MINS` | `step_book_mins()` in `booking.py:964` | Console_Booking | `_do_create_booking()` calls `create_booking()` |
| * | `_do_create_booking` | private fn in `booking.py:992` | Console_Booking + Console_Games | `create_booking(cid, member, staff, notes, planned_end)` → appends row; `_delete_session_game()` + `write_console_game()` (Session type) |

### Flow Logic

#### BOOK_LINK (optional booking link)
- User presses `▶️ Start Session` from Console Menu
- `prompt_book_console()` → `prompt_book_link()` shows today's confirmed/arrived bookings
- Staff can **link session** to a customer pre-booking (autofills console, member, game, duration)
- "⏭️ Booking မရှိဘဲ ဆက်သွား" → skips to console selection

#### BOOK_CONSOLE
- Shows only **Free** consoles (from `fetch_console_status()`)
- Staff picks console → extracted console ID (text before first paren)

#### BOOK_MEMBER
- Shows member list from `fetch_members()` + "0 (Guest)" option
- Supports partial text search
- **Duplicate session check**: If member already has Active/Scheduled session, goes to `BOOK_DUP_WARN` asking Proceed/Reselect

#### BOOK_GAME
- Shows games **installed on the selected console** (`get_games_on_console(cid)`)
- `🔄 SSD Transfer` button → redirects to `SSD_XFER_SSD` with `ssd_return_to_session=True`
- `⏭️ Skip Game` → skips to mins prompt
- After game selected → goes to `BOOK_MINS`

#### BOOK_MINS → Create
- Staff picks duration (30-360 mins) or Skip
- `_do_create_booking()`:
  1. `create_booking(cid, member, staff, notes=game, planned_end=HH:MM)` → appends row to **Console_Booking** (Status="Active")
  2. If game selected: `write_console_game(cid, game, "Session", notes)` → **Console_Games** (install_type="Session")
  3. If timer set: launches `_remind_loop()` asyncio task (fires at 5min before end with Extend/Done inline keyboard)
  4. If linked to customer booking: stores `[BK#ID]` in notes for end-tracking

---

## FLOW 2: End Session

**Entry point:** `BTN_END_SESSION` from Console Menu

### State Chain

```
END_SESSION_SELECT (one-step) → launch_session_sale()
```

| # | State | Handler Function | Sheet Tab | API Calls |
|---|-------|-----------------|-----------|-----------|
| 1 | `END_SESSION_SELECT` | `step_end_session()` in `console.py:251` | Console_Booking + Console_Games | `fetch_console_status()` → find Active; `end_booking(bk_id)` → sets EndTime+Done; `_delete_session_game(cid)`; POST to n8n |

### Flow Logic
1. `prompt_end_session()` shows all Active consoles with member name + duration
2. Staff picks console → `step_end_session()`:
   - Finds booking ID from `fetch_console_status()`
   - Calls `end_booking(bk_id)` → updates Console_Booking row (F=EndTime, G="Done")
   - Checks for SSD Transfer games on console (warns if any)
   - Deletes Session-type game entries
   - Looks up linked customer booking ID via `_replit_get(f"bookings?memberId={mbr}")`
   - Routes to `launch_session_sale()` → opens Sales Voucher flow

---

## FLOW 3: Staff Advance Booking (SBK)

**Entry point:** Admin Panel → `BTN_STAFF_BOOK` or Staff Hub → `BTN_SBK_NEW`

### State Chain

```
SBK_CONSOLE (72) → SBK_CUST_NAME (73) → SBK_DATE (74) → SBK_TIME (75) → SBK_DUR (76) → SBK_GAME (77) → SBK_CONFIRM (78) → DONE
```

### Detailed State Table

| # | State | Handler Function | Sheet/API | Actions |
|---|-------|-----------------|-----------|---------|
| 1 | `SBK_CONSOLE` | `step_sbk_console()` in `booking.py:173` | API: `_replit_get("sheets/consoles")` | Shows all consoles with live status (✅ Free / 🔴 Busy); fallback to `fetch_console_status()` |
| 2 | `SBK_CUST_NAME` | `step_sbk_cust_name()` in `booking.py:214` | Card_Wallet | Shows member list + "👤 Guest (Walk-in)" option |
| 3 | `SBK_DATE` | `step_sbk_date()` in `booking.py:235` | — | Collects phone (optional) then shows date picker: Today, Tomorrow, Day+2, Custom |
| 4 | `SBK_TIME` | `step_sbk_time()` in `booking.py:263` | — | Shows time slots 10:00–22:00; custom M/D/YYYY supported |
| 5 | `SBK_DUR` | `step_sbk_dur()` in `booking.py:317` | — | Duration picker: 30/60/90/120/150/180/240/300/360 |
| 6 | `SBK_GAME` | `step_sbk_game()` in `booking.py:360` | Game_Library | Shows game list from `fetch_games()` + Skip option |
| 7 | `SBK_CONFIRM` | `step_sbk_confirm()` in `booking.py:414` | API: `_replit_post("bookings", payload)` | **Phase 1**: Shows summary with SSD transfer warning + disc conflict check; **Phase 2**: On confirm → POST to API, notify staff group, fire n8n reminder |

### Key Behaviors in SBK_CONFIRM
- **SSD Transfer Warning**: If selected game not installed on console, checks `get_consoles_with_game()` and `fetch_console_games()` for SSD locations
- **Disc Conflict**: `check_disc_session_conflict()` → checks if all physical disc copies are in use at booking time
- **On Create**: POSTs to `_replit_post("bookings", payload)` with status="confirmed"; notifies `STAFF_NOTIFY_CHAT`; fires `_post_n8n_booking_reminder()` asyncio task

### Staff Booking Hub

| Function | Entry | Description |
|----------|-------|-------------|
| `cmd_staff_book_hub()` | Admin Panel | Shows pending + confirmed booking counts |
| `cmd_confirmed_bookings()` | Staff Hub | Lists confirmed bookings with Cancel button each; sorted today-first |

---

## FLOW 4: Console Management (CON)

**Entry point:** Admin Panel → `BTN_CON_MANAGE`

### State Chain

```
CON_MGMT_MENU (59) → CON_ADD_ID (60) → CON_ADD_TYPE (61) → CON_ADD_MULT (62) → done
                   → CON_DEL_SELECT (63) → done
                   → BTN_LIST_CONSOLE → view-only
```

### Detailed State Table

| # | State | Handler Function | Sheet Tab | API Calls |
|---|-------|-----------------|-----------|-----------|
| 1 | `CON_MGMT_MENU` | `step_con_mgmt_menu()` in `console_mgmt.py:28` | Setting | `get_consoles_from_setting()` reads Setting col H/I/J |
| 2a | `CON_ADD_ID` | `step_con_add_id()` in `console_mgmt.py:68` | Setting | Duplicate check via `get_consoles_from_setting()` |
| 2b | `CON_ADD_TYPE` | `step_con_add_type()` in `console_mgmt.py:86` | Setting | Type: PS4/PS5/VR |
| 2c | `CON_ADD_MULT` | `step_con_add_mult()` in `console_mgmt.py:100` | Setting | Multiplier: 1.0/1.5/2.0; calls `add_console_to_setting(id, type, mult)` |
| 3 | `CON_DEL_SELECT` | `step_con_del_select()` in `console_mgmt.py:126` | Setting | Calls `remove_console_from_setting(id)`; removes from `VALID_CONSOLES` set |

### Backing Functions

```python
add_console_to_setting(console_id, ctype, multiplier)
# → appends row to Setting sheet (H=console_id, I=type, J=multiplier)

remove_console_from_setting(console_id)
# → finds row in Setting col H, deletes it

get_consoles_from_setting()
# → reads Setting col H/I/J, returns list[dict] with id/type/mult
```

---

## FLOW 5: Game Install Management (GINST)

**Entry point:** Game Library Menu → `BTN_CONSOLE_INSTALL`

### State Chain

```
GINST_MENU (79) → GINST_VIEW_CONS (80) → view
                → GINST_ADD_CONS (81) → GINST_ADD_GAME (82) → GINST_ADD_TYPE (83) → save
                → GINST_DEL_CONS (84) → GINST_DEL_GAME (85) → delete
```

### Detailed State Table

| # | State | Handler Function | Sheet Tab | API Calls |
|---|-------|-----------------|-----------|-----------|
| 1 | `GINST_MENU` | `step_ginst_menu()` in `ginst.py:39` | Console_Games + Setting | `fetch_console_games()` for count |
| 2a | `GINST_VIEW_CONS` | `step_ginst_view_cons()` in `ginst.py:66` | Console_Games | `fetch_console_games()` filtered by console_id; `get_games_on_console()` |
| 2b | `GINST_ADD_CONS` | `step_ginst_add_cons()` in `ginst.py:87` | Setting | `get_consoles_from_setting()` for console list |
| 3b | `GINST_ADD_GAME` | `step_ginst_add_game()` in `ginst.py:115` | Console_Games + Game_Library | `fetch_games()` for game list; `fetch_console_games()` for duplicate check; `add_console_game()` + `update_game_library_install()` |
| 4b | `GINST_ADD_TYPE` | `step_ginst_add_type()` in `ginst.py:159` | Console_Games + Game_Library | Type: HDD/Disc/Portable SSD; saves both sheets |
| 2c | `GINST_DEL_CONS` | `step_ginst_del_cons()` in `ginst.py:191` | Console_Games | `fetch_console_games()` filtered |
| 3c | `GINST_DEL_GAME` | `step_ginst_del_game()` in `ginst.py:215` | Console_Games + Game_Library | `remove_console_game()` + `update_game_library_install(cid, False)` |

### Key: Dual Write Pattern
Every add/delete writes to **two sheets**:
1. `Console_Games` — record with Console_ID, Game_Title, Install_Type, Date
2. `Game_Library` — checkbox column for that console, cleared on delete

---

## FLOW 6: SSD Management (SSD)

**Entry point:** Console Menu → `BTN_SSD_MANAGE`

**SSD identifiers:**
- T1 (`Samsung T-7`)
- Blue (`Sandisk-1`)  
- Grey (`Sandisk-2`)

### State Chain

```
SSD_MENU (86) → SSD_VIEW_SSD (87)
              → SSD_ADD_SSD (88) → SSD_ADD_GAME (89) → SSD_ADD_TYPE (90)
              → SSD_DEL_SSD (91) → SSD_DEL_GAME (92)
              → SSD_XFER_SSD (93) → SSD_XFER_GAME (94) → SSD_XFER_CONS (95)
              → SSD_RET_CONS (96) → SSD_RET_GAME (97)
```

### Detailed State Table

| # | State | Handler Function | Sheet Tab | API Calls / Actions |
|---|-------|-----------------|-----------|---------------------|
| 1 | `SSD_MENU` | `step_ssd_menu()` in `ssd_disc.py:122` | Console_Games | `fetch_console_games()` to count per SSD |
| 2a | `SSD_VIEW_SSD` | `step_ssd_view()` in `ssd_disc.py:155` | Console_Games | `fetch_console_games()` filtered by SSD id |
| 2b | `SSD_ADD_SSD` | `step_ssd_add_ssd()` in `ssd_disc.py:179` | Game_Library | `fetch_game_library()` for game titles |
| 3b | `SSD_ADD_GAME` | `step_ssd_add_game()` in `ssd_disc.py:—` | Console_Games | Duplicate check then `write_console_game(ssd_id, game, "SSD Copy")` |
| 3c | `SSD_ADD_TYPE` | `step_ssd_add_type()` in `ssd_disc.py:—` | Console_Games | `write_console_game()` with chosen install type |
| 2d | `SSD_DEL_SSD` | `step_ssd_del_ssd()` in `ssd_disc.py:—` | Console_Games | Shows games on SSD |
| 3d | `SSD_DEL_GAME` | `step_ssd_del_game()` in `ssd_disc.py:—` | Console_Games | `delete_console_game(ssd_id, game)` |
| 2e | `SSD_XFER_SSD` | `step_ssd_xfer_ssd()` in `ssd_disc.py:—` | Console_Games | Shows games on source SSD |
| 3e | `SSD_XFER_GAME` | `step_ssd_xfer_game()` in `ssd_disc.py:—` | Console_Games + Game_Library | **Session shortcut**: if `ssd_return_to_session=True`, transfers directly to target console; else asks console |
| 4e | `SSD_XFER_CONS` | `step_ssd_xfer_cons()` in `ssd_disc.py:—` | Console_Games | Duplicate check then `write_console_game(cid, game, "SSD Transfer", "From SSD")` → removes from SSD |
| 2f | `SSD_RET_CONS` | `step_ssd_ret_cons()` in `ssd_disc.py:—` | Console_Games | Shows consoles with SSD Transfer games |
| 3f | `SSD_RET_GAME` | `step_ssd_ret_game()` in `ssd_disc.py:—` | Console_Games | `delete_console_game(cid, game)` — removes transfer record |

### Critical: SSD Transfer `move` Semantics
- **Transfer (SSD → Console)**: Writes to Console_Games with `install_type="SSD Transfer"`, then **removes** from SSD (not just copies)
- **Return (Console → SSD)**: Only removes the Console_Games record; does NOT re-add to SSD (staff must re-add manually if needed)
- **End Session Warning**: When ending session, bot checks for any SSD Transfer-type games on that console and warns staff

---

## FLOW 7: Disc Management (DISC)

**Entry point:** Game Library Menu → `BTN_DISC_RECORD`

### State Chain

```
DISC_SELECT (98) → DISC_SET_QTY (99)
```

| # | State | Handler Function | Sheet Tab | API Calls |
|---|-------|-----------------|-----------|-----------|
| 1 | `DISC_SELECT` | `step_disc_select()` in `ssd_disc.py:33` | Game_Library | `fetch_games()` for disc game list |
| 2 | `DISC_SET_QTY` | `step_disc_set_qty()` in `ssd_disc.py:68` | Game_Library | `set_game_disc_count(row_num, count)` → updates col D (Available Discs) |

### Disc Conflict Check (used in SBK_CONFIRM)
`check_disc_session_conflict(game_name, bk_time)`:
1. Looks up total disc count from Game_Library col D
2. Checks Console_Booking for Active sessions playing same game today
3. Compares active count vs total; if all busy, checks if any session's planned_end is before booking time
4. Returns warning message if conflict exists

---

## FLOW 8: Stock Management (STOCK + SI)

**Entry point:** Main Menu → `BTN_STOCK_UPDATE` or `/stockin`, `/stockout`, `/stock` commands

### State Chain

```
STOCK_PIN (25) → STOCK_MENU (26)
                     → STOCK_ITEM (27) → STOCK_QTY (28) → done [Stock Out]
                     → SI_ITEM (29) → SI_QTY (30) → SI_COST (31) → SI_CART (32) → SI_PAY (33) → SI_CONFIRM (34)
                                                                                         → SI_PAY_SPLIT (43) → SI_CONFIRM
```

### Detailed State Table

#### Stock Out Flow

| # | State | Handler Function | Sheet Tab | API Calls |
|---|-------|-----------------|-----------|-----------|
| 1 | `STOCK_PIN` | `step_stock_pin()` in `stock.py:46` | — | PIN verify vs `STOCK_ACCESS_PIN` env var; routes to stockin/stockout/menu |
| 2 | `STOCK_MENU` | `step_stock_menu()` in `stock.py:94` | Inventory | Stock Out / Stock In / Inventory View sub-menu |
| 3a | `STOCK_ITEM` | `step_stock_item()` in `stock.py:138` | Setting | `fetch_food_prices()` from Setting col D/E |
| 4a | `STOCK_QTY` | `step_stock_qty()` in `stock.py:159` | Stock_Out + Inventory | Appends row `[date, ref, item, qty, sell_price, total_val, cost_price, total_cogs]` to Stock_Out; `_update_inv_total_k1()`; API `_replit_get("sheets/inventory")` for low-stock alert |

#### Stock In Flow (with cart)

| # | State | Handler Function | Sheet Tab | API Calls |
|---|-------|-----------------|-----------|-----------|
| 1 | `SI_ITEM` | `step_si_item()` in `stock_in.py:27` | Setting | `fetch_food_prices()` |
| 2 | `SI_QTY` | `step_si_qty()` in `stock_in.py:44` | — | Quantity input (1+), shows default cost hint from `fetch_food_costs()` |
| 3 | `SI_COST` | `step_si_cost()` in `stock_in.py:69` | — | Unit cost input; adds `{item, qty, cost, total}` to cart |
| 4 | `SI_CART` | `step_si_cart()` in `stock_in.py:118` | — | Shows running cart; ➕ Add / ✔️ Finish options |
| 5 | `SI_PAY` | `step_si_pay()` in `stock_in.py:171` | — | Cash / KPay / Split payment |
| 5b | `SI_PAY_SPLIT` | `step_si_pay_split()` in `stock_in.py:202` | — | Cash portion input; KPay = Grand Total − Cash |
| 6 | `SI_CONFIRM` | `step_si_confirm()` in `stock_in.py:228` | Stock_In + Inventory | Appends each cart item as `[date, item, qty, cost, total, payment, "Bot"]` to Stock_In; `_update_inv_total_k1()` |

### Inventory View
- API: `_replit_get("sheets/inventory")` → returns items with name, current_stock, status, inv_value
- Shows 🟢 In Stock / 🟡 Low Stock / 🔴 Out of Stock / ⚫ No Stock
- Total inventory value at bottom

---

## FLOW 9: Console Status Board

**Entry point:** `BTN_STATUS_BOARD` from Console Menu or Main Menu

| Function | Sheet Tab | API Calls |
|----------|-----------|-----------|
| `cmd_console_status()` in `console.py:13` | Console_Booking + Console_Games + Setting | `_replit_get("sheets/consoles")` (primary); fallback to `fetch_console_status()` |

### Display
- Shows all consoles with: 🟢 Free / 🟡 Reserved (with time range + member) / 🔴 Active (with member + since time)
- Each console shows installed games from `fetch_console_games()` (excluding Session/SSD Transfer types)
- Count summary: Free, Active, Reserved tallies

---

## FLOW 10: Game Change Mid-Session

**Entry point:** Console Menu → `BTN_CHANGE_GAME`

### State Chain

```
GAME_CHANGE_CONS → GAME_CHANGE_GAME (done)
```

| # | State | Handler Function | Sheet Tab | API Calls |
|---|-------|-----------------|-----------|-----------|
| 1 | `GAME_CHANGE_CONS` | `step_game_change_cons()` in `console.py:148` | Console_Booking | `fetch_console_status()` for Active consoles |
| 2 | `GAME_CHANGE_GAME` | `step_game_change_game()` in `console.py:186` | Console_Games | `fetch_console_games()` for current session game; `get_games_on_console()`; `_delete_session_game()` + `add_console_game()` |

---

## Flow Summary Matrix

| Flow | Entry State | Exit State | Sheets Written | API POST | n8n |
|------|------------|------------|---------------|----------|-----|
| **Session Start** | `BOOK_LINK` | DONE | Console_Booking + Console_Games | — | Session reminder via `_remind_loop()` |
| **Session End** | `END_SESSION_SELECT` | Sales Voucher | Console_Booking (Done) + Console_Games (delete Session) | — | Session end |
| **Staff Booking** | `SBK_CONSOLE` | Main Menu | — | `POST /api/bookings` | Booking reminder via n8n |
| **Console CRUD** | `CON_MGMT_MENU` | Console Menu | Setting (H/I/J cols) | — | — |
| **Game Library** | `GAME_MENU` | Various | Game_Library + Console_Games | — | — |
| **Game Install** | `GINST_MENU` | Game Menu | Console_Games + Game_Library | — | — |
| **SSD Mgmt** | `SSD_MENU` | Console/Game Menu | Console_Games | — | — |
| **Disc Record** | `DISC_SELECT` | Game Menu | Game_Library (col D) | — | — |
| **Stock Out** | `STOCK_PIN` → `STOCK_MENU` | Main Menu | Stock_Out + Inventory | — | — |
| **Stock In** | `STOCK_PIN` → `STOCK_MENU` | Main Menu | Stock_In + Inventory | — | — |
| **Status Board** | (command) | Console Menu | Read-only (all) | — | — |
| **Game Change** | `GAME_CHANGE_CONS` | Console Menu | Console_Games | — | — |

---

## Key Implementation Patterns

### 1. Dual-Sheet Consistency
Game installs always write to **both** Console_Games (install record) AND Game_Library (checkbox column). Deletions clear both.

### 2. API + Sheet Fallback
Every read function has pattern: `_HAS_API → api_client.X()` → fallback to `gspread.X()`. API is optional; bot works with sheets-only.

### 3. Session-as-Install-Record
When session starts with a game, it creates a **temporary** Console_Games row with `install_type="Session"`. This row is deleted when session ends via `_delete_session_game()`.

### 4. SSD Transfer = Move (not Copy)
SSD → Console transfer **removes** game from SSD record. Return (Console → SSD) only deletes transfer record — no auto re-add to SSD.

### 5. Stock PIN Security
PIN is verified then immediately deleted from chat. Falls back to edit-then-warn if delete fails.

### 6. State Data Passing
All flow state stored in `context.user_data` dict (per-user, per-conversation). Cleared on cancel/done via `context.user_data.clear()`.
