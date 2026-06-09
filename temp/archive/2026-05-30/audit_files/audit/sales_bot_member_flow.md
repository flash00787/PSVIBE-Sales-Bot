# PSVibe Sale Bot — Member / TopUp / Session Flow Trace

> **Bot path:** `/root/psvibe-sale-bot/` on `5.223.81.16`
> **Generated:** 2026-05-28
> **Handler files:** `bot/handlers/members.py`, `bot/handlers/sales.py`, `bot/handlers/console.py`, `bot/handlers/discount.py`, `bot/handlers/booking.py`
> **State enum + wiring:** `bot/__init__.py` (BotState enum) + `bot/app.py` (ConversationHandler states)

---

## FLOW 1: NEW MEMBER REGISTRATION (NM_*)

**Entry points:** `/newmember` command, or `MM_MENU → BTN_FIRST_PURCHASE`
**Sheet tabs:** `Card_Wallet`, `TopUp_Log`
**Handler file:** `bot/handlers/members.py`

### NM_STAFF (Staff Selection)
- **Handler:** `members.py` → `prompt_nm_staff()` / `step_nm_staff()`
- **Sheet/API:** `Sheet: Staff` (via `fetch_staff()`)
- **What happens:** Staff list fetched from Staff sheet; user picks a staff name. Stored as `nm_staff` in user_data.
- **Next state:** NM_NAME

### NM_NAME (New Member — Name)
- **Handler:** `members.py` → `prompt_nm_name()` / `step_nm_name()`
- **Sheet:** None (text input only)
- **What happens:** Free-text name entry. Stored as `nm_name`.
- **Next state:** NM_PHONE

### NM_PHONE (New Member — Phone)
- **Handler:** `members.py` → `prompt_nm_phone()` / `step_nm_phone()`
- **Sheet:** None
- **What happens:** Phone number input, validated (≥7 digits). Stored as `nm_phone`.
- **Next state:** NM_EMAIL

### NM_EMAIL (New Member — Email)
- **Handler:** `members.py` → `prompt_nm_email()` / `step_nm_email()`
- **Sheet:** None
- **What happens:** Email input or skip. Auto-generates member ID via `next_member_id()`. Stored as `nm_email`, `nm_id`.
- **Next state:** NM_ID

### NM_ID (New Member — Member ID Confirmation)
- **Handler:** `members.py` → `prompt_nm_id()` / `step_nm_id()`
- **Sheet:** None
- **What happens:** Shows auto-generated ID. Staff can confirm (`BTN_CONFIRM_ID`) or type a custom ID.
- **Next state:** NM_AMT

### NM_AMT (New Member — Card Amount)
- **Handler:** `members.py` → `prompt_nm_amt()` / `step_nm_amt()`
- **Sheet:** `Sheet: Setting` (B20=price, B21=base_mins via `fetch_new_member_defaults()`)
- **What happens:** Shows default card price. Staff can:
  - Confirm default → go to payment (NM_KPAY)
  - Click `BTN_NM_CUSTOM` → type custom amount (re-prompts NM_AMT)
  - Click `BTN_NM_GIFT` → prompts admin PIN (NM_GIFT_PIN)
- **Next state:** NM_KPAY or NM_GIFT_PIN

### NM_GIFT_PIN (New Member — Gift PIN Verification)
- **Handler:** `members.py` → `step_nm_gift_pin()`
- **Sheet:** None (checks against `STOCK_ACCESS_PIN` config)
- **What happens:** Admin PIN verification for Gift/Free cards. Sets `nm_amt=0`, `nm_kpay=0`, `nm_cash=0`, `nm_mins` from Setting!B21, `nm_is_gift=True`.
- **Next state:** NM_CONFIRM

### NM_KPAY (New Member — Kpay Amount)
- **Handler:** `members.py` → `prompt_nm_kpay()` / `step_nm_kpay()`
- **Sheet:** None
- **What happens:** Kpay amount entry (max = card amount). Computes `nm_cash = nm_amt - nm_kpay`. Shows Review Your Entry summary.
- **Next state:** NM_REFERRAL (via prompt_nm_referral)

### NM_REFERRAL (New Member — Referral Code)
- **Handler:** `members.py` → `prompt_nm_referral()` / `step_nm_referral()`
- **Sheet read:** `Card_Wallet` col Q (referral codes) via `member_sh.get_all_values()`
- **What happens:** Optional referral code entry. Validated 4–20 chars. Lookup referrer in Card_Wallet col Q. On match: stores `nm_referral_code` + `nm_referrer_id`.
- **Next state:** NM_CONFIRM

### NM_CONFIRM (New Member — Confirm & Save)
- **Handler:** `members.py` → `_show_nm_confirm()` / `step_nm_confirm()`
- **Sheet writes (background):**
  - **Card_Wallet:** Col A(row_no), B(nm_id), C(nm_name), D(phone), K(nm_staff), M(email)
  - **TopUp_Log:** Col A(today), B(nm_id), C("New Member"), E(amt), F(kpay), G(cash), H(mins + ref_bonus), I(type), J(nm_staff)
  - **Effective Rate:** `update_member_effective_rate(nm_id, initial_rate)` → Card_Wallet rate column
  - **Referral bonus (if applicable):** Extra TopUp_Log row for referrer (+30 mins)
- **Receipt:** Saved via `save_receipt_json()` → `RECEIPTS_DIR/nv/{nm_vid}.json`
- **Next state:** MAIN_MENU (via `show_main_menu()`)

---

## FLOW 2: TOP-UP (TU_*)

**Entry points:** `/topup` command, or `MM_MENU → BTN_TOP_UP`, or auto-routed from SESSION_SHORTFALL
**Sheet tabs:** `TopUp_Log`, `Card_Wallet`
**Handler file:** `bot/handlers/members.py`

### TU_MEMBER (Top-Up — Select Member)
- **Handler:** `members.py` → `prompt_tu_member()` / `step_tu_member()`
- **Sheet read:** `Card_Wallet` via `fetch_members()` + `fetch_member_data(member_id)`
- **API:** None
- **What happens:** Member selection (list or search). Fetches member data: rank, total_spend, phone, name, wallet_mins. Also fetches rank thresholds + bonus table. Stored as `tu_id`, `tu_rank`, `tu_total_spend`, etc.
- **Next state:** TU_AMT

### TU_AMT (Top-Up — Amount)
- **Handler:** `members.py` → `prompt_tu_amt()` / `step_tu_amt()`
- **Sheet read:** `Sheet: Setting` (base_rate via `fetch_base_rate()`), bonus table
- **What happens:** Shows member rank, progress to next tier, bonus table. Staff enters top-up amount (Ks). Computes:
  - `base_mins = round((amt * 60) / hourly_rate)`
  - `bonus_mins = get_bonus_mins(rank, amt, bonus_table)`
  - `total_mins = base_mins + bonus_mins`
- **Next state:** TU_KPAY

### TU_KPAY (Top-Up — Kpay Amount)
- **Handler:** `members.py` → `prompt_tu_kpay()` / `step_tu_kpay()`
- **Sheet:** None
- **What happens:** Kpay amount entry. Shows Review Your Entry including rank bonus, next-tier progress.
- **Next state:** TU_CONFIRM

### TU_CONFIRM (Top-Up — Confirm & Save)
- **Handler:** `members.py` → `step_tu_confirm()`
- **Sheet writes (background):**
  - **TopUp_Log:** Col A(today), B(tu_id), C(current_tier), E(amt), F(kpay), G(cash), H(total_mins), I("Top Up")
  - **Card_Wallet:** Updates effective rate via `update_member_effective_rate(tu_id, new_rate)`
- **API/Receipt:** `save_receipt_json()` → `RECEIPTS_DIR/nv/{tu_vid}.json`
- **Next state:** MAIN_MENU (or returns to session sale flow if `after_topup == "console_sale"`)

---

## FLOW 3: DAILY SALES — NEW SESSION (MEMBER → SALE_CONFIRM)

**Entry points:** `/sales` command, or main menu `BTN_DAILY_SALES`
**Sheet tabs:** `Sales_Daily`, `Stock_Out_Log`, `Promotions_Log`
**Handler file:** `bot/handlers/sales.py`

### MEMBER (Sales — Select Member)
- **Handler:** `sales.py` → `prompt_member()` / `step_member()`
- **Sheet read:** `Card_Wallet` via `fetch_members()`
- **What happens:** Member selection with search. Guest `0 (Guest)` is always pinned. For members, also checks if member is in an active session (`_check_member_in_session` → DS_MEMBER_IN_SESSION).
- **Next state:** CONSOLE

### DS_MEMBER_IN_SESSION (Member Already in Active Session)
- **Handler:** `sales.py` → `step_ds_member_in_session()`
- **API:** `_replit_get("sheets/consoles")` for active console status
- **What happens:** Detects member already has an active session. Shows option to end that session and start sales flow for it (via `_end_single_session_and_launch → launch_session_sale`).
- **Next state:** CONSOLE (or routed to launch_session_sale)

### CONSOLE (Sales — Select Console)
- **Handler:** `sales.py` → `prompt_console()` / `step_console()`
- **Sheet read:** `Sheet: Setting` (valid consoles + multipliers via `fetch_console_multiplier()`)
- **What happens:** Console selection. Checks if console is already in an active session (`_check_console_in_session` → DS_CONSOLE_IN_SESSION). For members, shows wallet balance.
- **Next state:** MINS (or DS_CONSOLE_IN_SESSION)

### DS_CONSOLE_IN_SESSION (Console Already in Active Session)
- **Handler:** `sales.py` → `step_ds_console_in_session()`
- **API:** `_replit_get("sheets/consoles")`
- **What happens:** Detects console already has an active session. Staff can end it and continue with sales.
- **Next state:** MINS

### MINS (Sales — Play Minutes)
- **Handler:** `sales.py` → `prompt_mins()` / `step_mins()`
- **Sheet read:** `Sheet: Setting` (base_rate via `fetch_base_rate()`); inventory for stock-based food filtering
- **What happens:** Minutes input. Fetches food prices filtered by stock. Initializes `food_items = []`.
- **Next state:** FOOD_MENU

### FOOD_MENU (Sales — Food & Drinks Selection)
- **Handler:** `sales.py` → `prompt_food_menu()` / `step_food_menu()`
- **Sheet read:** Food prices + inventory stock map
- **What happens:** Food selection menu with running cart. Can add items (→ FOOD_QTY), clear cart, or Done.
- **Next state:** FOOD_QTY or CONFIRM_SUMMARY

### FOOD_QTY (Sales — Food Quantity)
- **Handler:** `sales.py` → `step_food_qty()`
- **Sheet:** None (stock validation against in-memory map)
- **What happens:** Quantity entry with stock limit enforcement.
- **Next state:** FOOD_MENU

### CONFIRM_SUMMARY (Sales — Review Summary)
- **Handler:** `sales.py` → `prompt_confirm()` / `step_confirm()`
- **Sheet:** None (all computation)
- **What happens:** Shows full summary:
  - **Guest:** `game_amt = round(mins × base_rate × multiplier / 60)`, net = game + food
  - **Member:** Wallet deduction calculation (`effective_cost_mins = play_mins × multiplier`). If insufficient → SESSION_SHORTFALL
  - **Member + Cash Down:** Shows wallet fully depleted + cash for shortfall
- **Next state:** DISCOUNT or SESSION_SHORTFALL

### DISCOUNT (Sales — Discount / Promotion)
- **Handler:** `discount.py` → `prompt_discount()`
- **API:** Promotions from Replit API (`fetch_promotions_cached()`)
- **What happens:** Shows active promotions + manual discount option + skip. Can branch to:
  - `BTN_PROMO_APPLY` → PROMO_SELECT
  - `BTN_MANUAL_DISC` → type discount amount
  - `BTN_SKIP_DISC` → skips discount, goes to KPAY_AMT
- **Next state:** PROMO_SELECT or KPAY_AMT

### PROMO_SELECT (Sales — Promotion Selection)
- **Handler:** `discount.py` → `prompt_promo_select()` / `step_promo_select()`
- **API:** Replit promotions API
- **What happens:** Staff picks a promotion. For bundle/FOC promos → BUNDLE_FOC. Applies discount/bonus to context.
- **Next state:** KPAY_AMT or BUNDLE_FOC

### KPAY_AMT (Sales — Kpay Amount)
- **Handler:** `sales.py` → `prompt_kpay()` / `step_kpay()`
- **Sheet:** None
- **What happens:** Kpay amount (max = net_total). Shows Review Your Entry.
- **Next state:** SALE_CONFIRM

### SALE_CONFIRM (Sales — Confirm & Save)
- **Handler:** `sales.py` → `step_sale_confirm()`
- **Sheet writes (background):**
  - **Sales_Daily:** Col A(today), B(v_no), C(m_id), D(c_id), E(play_mins), F(game_amt), G(food_total), H(discount), I(net_total), J(kpay), K(cash), N(wallet_deduct), O(staff)
  - **Stock_Out_Log:** Per food item → today, v_no, name, qty, unit_price, subtotal, cost, total_cost
  - **Inventory:** Updated via Replit API (`_update_inv_total_k1()`, `_replit_get("sheets/inventory?nocache=1")`)
  - **Promotions_Log:** If promo applied → Replit API
  - **Card_Wallet:** Bonus mins added to member wallet col H
- **API calls (async background):**
  - Mark linked booking as completed (Replit PATCH)
  - Waitlist notify for console (Replit POST)
  - Session-end customer notification (Replit POST + Telegram)
  - Low balance alert check
- **Receipt:** `save_receipt_json()` → `RECEIPTS_DIR/nv/{v_no}.json`
- **Next state:** MAIN_MENU

---

## FLOW 4: SESSION END → SALES BRIDGE (Console Booking → Daily Sales)

**Entry point:** Console Menu → `BTN_END_SESSION`
**Sheet tabs:** `Sales_Daily` (via launch_session_sale), Console bookings
**Handler files:** `bot/handlers/console.py` + `bot/handlers/sales.py`

### END_SESSION_SELECT (End Session — Pick Active Console)
- **Handler:** `console.py` → `prompt_end_session()` / `step_end_session()`
- **API:** `fetch_console_status()` → reads Sheet + PostgreSQL reservations
- **What happens:** Lists all active consoles with member, duration. Staff picks one. Calls `end_booking(bk_id)` to end the booking. Deletes Session game entry. Shows session summary (console, member, start, end, duration). Then auto-routes to `launch_session_sale()`.
- **Next state:** AUTO → launch_session_sale() → routes to ADJUST_TIME or FOOD_MENU

### ADJUST_TIME (Adjust Time — Optional override)
- **Handler:** `sales.py` → `prompt_adjust_time()` / `step_adjust_time()`
- **Sheet:** None
- **What happens:** Optional step after session end — allows adjusting actual played minutes before food selection. Default = session duration.
- **Next state:** FOOD_MENU

### SESSION_SHORTFALL (Wallet Insufficient — Top Up / Cash Down / Skip)
- **Handler:** `sales.py` → `prompt_session_shortfall()` / `step_session_shortfall()`
- **Sheet:** None (computation from user_data)
- **What happens:** When member wallet < effective_cost_mins. Three choices:
  - **BTN_TOPUP_SESSION:** Snapshots session state → routes to TU_AMT (Top-Up flow). After top-up, returns to session sale continuation.
  - **BTN_CASH_DOWN:** Wallet fully used (wallet_play_mins = wallet_bal / multiplier), remainder as cash. Routes to FOOD_MENU.
  - **BTN_SKIP_SALES:** Clears session data, returns to console menu.
- **Next state:** TU_AMT or FOOD_MENU or CONSOLE_MENU

---

## FLOW 5: CONSOLE BOOKING (Staff Advance Booking)

**Entry points:** `/newbooking` command, or Admin Panel booking
**Sheet tabs:** Replit bookings API
**Handler file:** `bot/handlers/booking.py`

### SBK_CONSOLE (Booking — Select Console)
- **Handler:** `booking.py` → `step_sbk_console()`
- **API:** Console list from Sheet/Replit
- **What happens:** Staff picks a console for advance booking.
- **Next state:** SBK_CUST_NAME

### SBK_CUST_NAME (Booking — Customer Name)
- **Handler:** `booking.py` → `step_sbk_cust_name()`
- **Sheet:** None
- **What happens:** Customer name input. `BTN_SBK_SKIP_PHONE` available.
- **Next state:** SBK_DATE

### SBK_DATE (Booking — Date)
- **Handler:** `booking.py` → `step_sbk_date()`
- **Sheet:** None
- **What happens:** Today / Tomorrow / Custom date selection.
- **Next state:** SBK_TIME

### SBK_TIME (Booking — Time)
- **Handler:** `booking.py` → `step_sbk_time()`
- **Sheet:** None
- **What happens:** Time slot selection (hour blocks).
- **Next state:** SBK_DUR

### SBK_DUR (Booking — Duration)
- **Handler:** `booking.py` → `step_sbk_dur()`
- **Sheet:** None
- **What happens:** Duration selection (30/60/90/120/180/240 mins).
- **Next state:** SBK_GAME

### SBK_GAME (Booking — Game Selection)
- **Handler:** `booking.py` → `step_sbk_game()`
- **API:** Games on console (installed games list)
- **What happens:** Pick game for booking. Can skip.
- **Next state:** SBK_CONFIRM

### SBK_CONFIRM (Booking — Confirm)
- **Handler:** `booking.py` → `step_sbk_confirm()`
- **API:** Replit API → POST create booking (via `create_booking()`)
- **Webhook:** `N8N_BOOKING_WEBHOOK` triggered after booking creation
- **Sheet:** None (all booking data goes through Replit API → PostgreSQL)
- **Next state:** MAIN_MENU

---

## FLOW 6: CUSTOMER-SIDE BOOKING (via Booking Link)

**Entry point:** Shared booking link (customer-facing)
**Handler file:** `bot/handlers/booking.py`

### BOOK_LINK (Customer Booking — Link Entry)
- **Handler:** `booking.py` → `prompt_book_link()` / `step_book_link()`
- **API:** Free consoles list from Sheet
- **What happens:** Customer clicks shared link. Shows free consoles or message if none available.
- **Next state:** BOOK_CONSOLE

### BOOK_CONSOLE (Customer Booking — Select Console)
- **Handler:** `booking.py` → `step_book_console()`
- **API:** Console status
- **What happens:** Console selection. Checks for duplicate active sessions.
- **Next state:** BOOK_MEMBER

### BOOK_MEMBER (Customer Booking — Member ID)
- **Handler:** `booking.py` → `step_book_member()`
- **API:** Member lookup
- **What happens:** Member ID input (or guest). Validates membership.
- **Next state:** BOOK_GAME

### BOOK_GAME (Customer Booking — Game)
- **Handler:** `booking.py` → `prompt_book_game()` / `step_book_game()`
- **API:** Games on selected console
- **What happens:** Game selection.
- **Next state:** BOOK_MINS

### BOOK_MINS (Customer Booking — Duration)
- **Handler:** `booking.py` → `prompt_book_mins()` / `step_book_mins()`
- **Sheet:** None
- **What happens:** Duration selection.
- **Next state:** BOOK_DUP_WARN (if duplicate) or auto-create booking

### BOOK_DUP_WARN (Customer Booking — Duplicate Warning)
- **Handler:** `booking.py` → `step_book_dup_warn()`
- **API:** Active bookings check
- **What happens:** Warns if customer already has an active booking. Can proceed or cancel.
- **Next state:** MAIN_MENU or booking creation

---

## SUMMARY: SHEET TAB REFERENCE

| Sheet Tab | States Writing to It | Columns Written |
|---|---|---|
| **Card_Wallet** | NM_CONFIRM, TU_CONFIRM | A(row_no), B(id), C(name), D(phone), H(balance via bonus), K(staff), M(email), rate columns |
| **TopUp_Log** | NM_CONFIRM, TU_CONFIRM, TU_CONFIRM (referral) | A(date), B(id), C(tier/type), E(amt), F(kpay), G(cash), H(mins), I(type), J(staff) |
| **Sales_Daily** | SALE_CONFIRM | A(date), B(v_no), C(m_id), D(c_id), E(mins), F(game_amt), G(food_total), H(discount), I(net_total), J(kpay), K(cash), N(wallet_deduct), O(staff) |
| **Stock_Out_Log** | SALE_CONFIRM | date, v_no, item_name, qty, unit_price, subtotal, cost, total_cost |
| **Promotions_Log** | SALE_CONFIRM | (via Replit API) date, voucher_no, promo_id, promo_title, member_id, etc. |
| **Setting** (read-only for these flows) | NM_AMT, MINS, CONFIRM_SUMMARY | B20(price), B21(mins), base_rate, console list, multipliers |

## SUMMARY: API CALLS

| API/Webhook | Trigger State | Method | Purpose |
|---|---|---|---|
| `sheets/consoles` | END_SESSION_SELECT, DS_MEMBER_IN_SESSION, DS_CONSOLE_IN_SESSION | GET | Console status (live) |
| `sheets/promotions` | DISCOUNT, PROMO_SELECT | GET | Active promotions |
| `sheets/inventory` | MINS, FOOD_MENU | GET | Stock levels for food filtering |
| `sheets/promotions-log` | SALE_CONFIRM | POST | Log promotion application |
| `bookings/{id}/status` | SALE_CONFIRM | PATCH | Mark linked booking as completed |
| `waitlist/notify` | SALE_CONFIRM | POST | Notify next waitlist customer |
| `session-end-notify` | SALE_CONFIRM | POST | Send session-end notification to customer bot |
| `N8N_SESSION_WEBHOOK` | (booking start) | POST | n8n webhook for session start |
| `N8N_BOOKING_WEBHOOK` | SBK_CONFIRM | POST | n8n webhook for new booking |
| `save_receipt_json()` | NM_CONFIRM, TU_CONFIRM, SALE_CONFIRM | local fs | Save receipt JSON locally |
| `get_receipt_kb()` | NM_CONFIRM, TU_CONFIRM, SALE_CONFIRM | — | Generate receipt download button |
| `update_member_effective_rate()` | NM_CONFIRM, TU_CONFIRM | Sheet write | Update Card_Wallet rate column |
| `end_booking()` | END_SESSION_SELECT | Replit API | End a console booking |

---

*End of flow trace. Total states covered: 35+*
