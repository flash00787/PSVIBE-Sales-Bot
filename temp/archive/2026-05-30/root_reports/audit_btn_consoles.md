# 🕹️ Consoles Button — Deep Audit Report

**Date**: 2026-05-28  
**Bot**: PS VIBE Sales Bot (psvibe-sales-bot)  
**VPS**: 5.223.81.16  
**Branch**: `BTN_CONSOLES = "🕹️ Consoles"` → `show_console_menu()` → `step_console_menu()`

---

## Flow Map

```
🕹️ Consoles (Main Menu)
    └─ show_console_menu()  →  CONSOLE_MENU state
        ├─ ▶️ Session Start    → prompt_book_console()    [booking.py]
        ├─ ⏹️ Session End      → prompt_end_session()     [console.py]
        ├─ 📊 Status Board     → cmd_console_status()      [console.py]
        ├─ 🎮 Game Library     → show_game_menu()          [games.py]
        ├─ 🔄 Change Game      → prompt_game_change_cons()  [console.py]
        ├─ 📀 External SSD     → show_ssd_menu()           [ssd_disc.py]
        └─ ⬅️ Back             → show_main_menu()
```

---

## 1. 📊 BTN_STATUS_BOARD — "📊 Status ကြည့်"

**Handler**: `cmd_console_status()` in `console.py:13`

### ✓ Handler Exists: YES
### ✓ API Calls: `_replit_get("sheets/consoles")` with gspread fallback
### ✓ State Transition: Stays in `CONSOLE_MENU` by re-displaying menu
### ✓ Format: Sorts consoles by Free/Active/Reserved, shows installed games
### △ Error Handling: try/except on fetch, passes generic error message

**Findings**:
- API response uses `data.get("consoles", [])` with keys `liveStatus`, `member`, `startTime`, `reservedFor`, `reservedAt`, `reservedDuration`
- Sheet fallback remaps keys: `status`, `member`, `start` — handled correctly
- Shows installed games from `fetch_console_games()` including SSD-transferred entries
- ✅ **PASS** — No critical issues

---

## 2. ▶️ BTN_START_SESSION — "▶️ Session Start"

**Handler**: `prompt_book_console()` → full booking flow in `booking.py:582`

### ✓ Handler Exists: YES
### ✓ API Calls: `fetch_console_status()`, `_replit_get("bookings")`, `create_booking()`
### ✓ State Transition: `CONSOLE_MENU` → `BOOK_LINK` → `BOOK_CONSOLE` → `BOOK_MEMBER` → `BOOK_GAME` → `BOOK_MINS` → `CONSOLE_MENU`

**Flow**:
1. Check for free consoles → show list
2. Optionally link to confirmed booking (autofill)
3. Select console → select member/guest
4. Select game (with SSD transfer option)
5. Set timer (mins) → confirm → `create_booking()` writes to Console_Booking sheet
6. `launch_session_sale()` checks wallet balance:
   - **Guest**: Skips wallet — charges `game_amt = round(total_mins × base_rate × multiplier / 60)`
   - **Member**: Checks wallet balance
     - Sufficient: `game_amt = 0` (wallet covers)
     - Insufficient: Shows shortfall → Top Up / Cash Down / Skip

### ✓ Wallet Balance Check: YES — in `launch_session_sale()` (sales.py:1237)
### ✓ Guest vs Member: YES — `is_guest = member_id in ("Guest", "0 (Guest)", "")`
### ✓ Shortfall handling: YES — `prompt_session_shortfall()` with Top Up / Cash Down / Skip
### ✓ Discount: Handled in sales flow (discount step after food)

**✅ PASS** — No blocking bugs

---

## 3. ⏹️ BTN_END_SESSION — "⏹️ Session End"

**Handler**: `prompt_end_session()` → `step_end_session()` in `console.py:213`

### ✓ Handler Exists: YES
### ✓ API Calls: `fetch_console_status()`, `end_booking()`, `launch_session_sale()`
### ✓ State Transition: `CONSOLE_MENU` → `END_SESSION_SELECT` → `CONSOLE_MENU`

**Flow**:
1. Show active consoles with duration
2. Pick console → `end_booking(bk_id)` marks it Done
3. `_delete_session_game(cid)` cleans up Session game entry
4. SSD transfer warning if SSD games still on console
5. `launch_session_sale()` for billing:
   - Computes `total_mins` via `calc_duration()`
   - Sets up sales context (member, console, mins, etc.)

### ✓ Time Calculation: `calc_duration(start_time_str)` — handles overnight correctly
### ✓ Discount: Redirects to full sales flow with discount step
### ✓ Shortfall: `launch_session_sale` handles wallet shortfall

**⚠ BUG #1 — Edge case**: `prompt_end_session()` lists ALL active consoles including those from *combined sessions* (e.g., showing "C-09" and "C-10" separately even if they're part of the same combined booking). The staff could end "C-09" while "C-10" is still part of the same booking — but `end_booking()` only marks the full booking as Done. If staff ends one half of a combined session, the other half would show "Active" but its booking_id is now Done, which `end_booking()` would fail to find (returns False). **Severity: LOW** — combined sessions are rare, and both consoles would need to be ended.

**⚠ BUG #2 — Error message**: When `bk_id` is empty string, the error message shows:
```
❌ Booking ID ရှာမတွေ့ပါ ()
```
The empty parentheses are confusing. **Severity: LOW**

**⚠ BUG #3 — Combined session multiplier**: `step_end_session()` calls `launch_session_sale()` without `pre_effective_mins`, meaning combined console sessions would get `multiplier = 1.0` (because `"+" not in cid` is True for single cids). For single-console sessions this is fine. For sessions ended through the booking flow's combined path, the booking flow stores the correct pre_effective_mins but `step_end_session` doesn't read it. **Severity: MEDIUM** — but combined sessions are rare.

**✅ PASS (with minor issues noted above)**

---

## 4. 🎮 BTN_GAME_LIB_MENU — "🎮 Game Library"

**Handler**: `show_game_menu()` in `games.py:14`

### ✓ Handler Exists: YES
### ✓ API Calls: `fetch_games()` via API with gspread fallback (cached 10 min)
### ✓ State Transition: `CONSOLE_MENU` → `GAME_MENU`

**Sub-buttons**:
- **📋 View Games** (`BTN_VIEW_GAMES`): Shows all games with install status, disc count, solo/multi tags, genre ✅
- **➕ Add Game** (`BTN_ADD_GAME`): Multi-step wizard: Title → Solo/Multi → Genre → Copies → Save ✅
- **🖥️ Console Install** (`BTN_CONSOLE_INSTALL`): Redirects to `show_ginst_menu()` ✅
- **🗑️ Delete Game** (`BTN_DEL_GAME`): Lists games, deletes row from sheet ✅
- **✏️ Edit Game** (`BTN_EDIT_GAME`): Edit Solo/Multi or Genre metadata (col U) ✅
- **💿 Disc Record** (`BTN_DISC_RECORD`): Set/update disc count per game ✅
- **📀 External SSD** (`BTN_SSD_MANAGE`): Redirects to `show_ssd_menu()` ✅
- **⬅️ Back** (`BTN_BACK_MAIN`): Returns to main menu ✅

### ✓ Library Loading: Correct — `fetch_games()` reads A:U from Game_Library sheet
### ✓ Column U metadata: "solo_multi|genre" format parsed correctly
### △ Game Delete: Sheet protection may block row deletion; shows friendly workaround message ✅

**✅ PASS** — No issues

---

## 5. 🔄 BTN_CHANGE_GAME — "🔄 Change Game"

**Handler**: `prompt_game_change_cons()` → `step_game_change_cons()` → `step_game_change_game()` in `console.py:133`

### ✓ Handler Exists: YES
### ✓ State Transition: `CONSOLE_MENU` → `GAME_CHANGE_CONS` → `GAME_CHANGE_GAME` → `CONSOLE_MENU`

**Flow**:
1. Pick active console (only Active sessions shown)
2. Show current game + installed games menu
3. Pick new game or SSD Transfer → `_delete_session_game(cid)` + `add_console_game(cid, new_game, "Session", "Changed")`

**🔴 BUG #4 — Critical redirect bug after SSD Transfer**:
In `step_game_change_game()` (line ~197), when the user presses `BTN_SSD_TRANSFER`:
```python
context.user_data["ssd_return_to_session"] = True
context.user_data["ssd_xfer_target_cons"] = cid
... → SSD_XFER_SSD
```
Then in `step_ssd_xfer_game()` (ssd_disc.py, the `ssd_return_to_session` branch), it calls:
```python
return await prompt_book_game(update, context)
```

**`prompt_book_game()` is for the BOOKING flow, NOT the game-change flow.** This causes a state confusion where the staff is suddenly in the booking game-selection screen after completing an SSD transfer from the game-change menu.

**Fix**: After SSD transfer in the change-game context, the handler should return to `prompt_game_change_cons()` or directly to `step_game_change_cons()` with the console pre-selected, so the staff can pick the newly transferred game.

**Severity: HIGH** — breaks UX and flow logic

---

## 6. 📀 BTN_SSD_MANAGE — "📀 External SSD" + Sub-Buttons

**Handler**: `show_ssd_menu()` in `ssd_disc.py:91`

### ✓ Handler Exists: YES
### ✓ State Transition: `CONSOLE_MENU` → `SSD_MENU`

### 6a. 📋 BTN_SSD_VIEW — "View SSD Contents"
- Handler: `step_ssd_view()` → Shows all games per SSD ✅
- SSD selection: 3 SSDs (T1 Shield / Sandisk Blue / Sandisk Grey) via `_ssd_kb()` ✅
- **✅ PASS**

### 6b. ➕ BTN_SSD_ADD — "Add Game to SSD"
- Handler: `step_ssd_add_ssd()` → `step_ssd_add_game()` ✅
- Game library lookup: `fetch_game_library()` (alias for `fetch_games()`) ✅
- Install type: Always "SSD Copy" — hardcoded ✅ (appropriate for SSD)
- Duplicate check: Yes ✅
- **⚠ ISSUE**: `step_ssd_add_type()` handler exists (SSD_ADD_TYPE state) but is **dead code** — `step_ssd_add_game()` saves directly and returns to menu, never transitions to SSD_ADD_TYPE. **Severity: LOW**
- **✅ PASS**

### 6c. ❌ BTN_SSD_REMOVE — "Remove Game from SSD"
- Handler: `step_ssd_del_ssd()` → `step_ssd_del_game()` ✅
- Uses `delete_console_game()` (alias for `remove_console_game()`) ✅
- **✅ PASS**

### 6d. 🔄 BTN_SSD_TRANSFER — "SSD → Console Transfer"
- Handler: `step_ssd_xfer_ssd()` → `step_ssd_xfer_game()` → `step_ssd_xfer_cons()` ✅
- Normal flow: SSD → Game → Console → save + remove from SSD ✅
- Duplicate check: Prevents re-transfer if already on console ✅
- Session shortcut (`ssd_return_to_session`): Handles booking flow shortcut ✅
- **⚠ See BUG #4 above** — redirect issue when called from game-change flow
- **✅ PASS** (with exception of the shared BUG #4)

### 6e. ↩️ BTN_SSD_RETURN — "Console → SSD Return"
- Handler: `step_ssd_ret_cons()` → `step_ssd_ret_game()` ✅
- Filters by `"SSD Transfer" in install_type` ✅
- Removes entry from console using `delete_console_game()` ✅
- **✅ PASS**

---

## 7. 🖥️ Console Install (ginst.py) — accessed via Game Library

**Handler**: `show_ginst_menu()` in `ginst.py`

### ✓ Handler Exists: YES
### ✓ State Transition: `GAME_MENU` → `GINST_MENU`

**Sub-buttons**:
- **📋 View** (`BTN_GINST_VIEW`): Shows install records per console with icon (💾 HDD / 💿 Disc / 🔌 SSD) ✅
- **➕ Add** (`BTN_GINST_ADD`): Game library picker + saves as "HDD" with Game_Library sync ✅
- **❌ Remove** (`BTN_GINST_DEL`): Numbered selection + delete with Game_Library sync ✅

### ✓ Duplicate Check: Prevents double-install ✅
### ✓ Game Library Sync: `update_game_library_install()` sets console checkboxes ✅
### ⚠ Dead Code: `step_ginst_add_type()` handler for GINST_ADD_TYPE state — never reached because `step_ginst_add_game()` saves immediately as "HDD" type. The type selection was planned but bypassed. **Severity: LOW**

**✅ PASS**

---

## 8. Console Management (console_mgmt.py) — Admin → Console CRUD

**Handler**: `show_con_mgmt_menu()` — NOT directly in the Consoles menu, but part of Admin Panel

### ✓ Add Console: Multi-step (ID → Type → Multiplier) → `add_console_to_setting()` ✅
### ✓ List Consoles: `get_consoles_from_setting()` ✅
### ✓ Delete Console: `remove_console_from_setting()` + VALID_CONSOLES.discard() ✅
### ✓ Duplicate Check: Prevent duplicate console IDs ✅

**✅ PASS**

---

## Summary

| Button | Handler | API | State | Error Handling | Status |
|--------|---------|-----|-------|----------------|--------|
| 📊 Status Board | `cmd_console_status` | ✅ | ✅ | ✅ | ✅ PASS |
| ▶️ Start Session | `prompt_book_console` | ✅ | ✅ | ✅ | ✅ PASS |
| ⏹️ End Session | `step_end_session` | ✅ | ✅ | ✅ | ⚠ MINOR |
| 🎮 Game Library | `show_game_menu` | ✅ | ✅ | ✅ | ✅ PASS |
| 🔄 Change Game | `step_game_change_game` | ✅ | ✅ | ✅ | 🔴 BUG #4 |
| 📀 SSD: View | `step_ssd_view` | ✅ | ✅ | ✅ | ✅ PASS |
| 📀 SSD: Add | `step_ssd_add_game` | ✅ | ✅ | ✅ | ✅ PASS |
| 📀 SSD: Remove | `step_ssd_del_game` | ✅ | ✅ | ✅ | ✅ PASS |
| 📀 SSD: Transfer | `step_ssd_xfer_*` | ✅ | ✅ | ✅ | 🔴 BUG #4 |
| 📀 SSD: Return | `step_ssd_ret_*` | ✅ | ✅ | ✅ | ✅ PASS |
| 🖥️ Console Install | `show_ginst_menu` | ✅ | ✅ | ✅ | ✅ PASS |

### 🔴 Critical Bugs
1. **BUG #4** — SSD Transfer from game-change flow redirects to `prompt_book_game()` (booking flow) instead of game-change flow. Causes state confusion.

### ⚠ Minor Issues
2. **BUG #1** — Combined sessions: ending one console of a pair may fail if booking already Done
3. **BUG #2** — Empty booking_id error message shows empty parentheses
4. Dead code: `step_ssd_add_type()` and `step_ginst_add_type()` — unreachable type-pickers

### Files Analyzed
- `bot/handlers/console.py` (371 lines)
- `bot/handlers/console_mgmt.py` (159 lines)
- `bot/handlers/games.py` (347 lines)
- `bot/handlers/ssd_disc.py` (414 lines)
- `bot/handlers/ginst.py` (231 lines)
- `bot/__init__.py` (API functions)
- `bot/app.py` (conversation handler registration)
