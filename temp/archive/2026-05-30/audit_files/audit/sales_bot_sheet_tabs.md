# Sales Bot — Google Sheet Tab Verification Report

**Date:** 2026-05-28  
**Sheet ID:** `1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA`  
**Sheet Title:** PS VIBE - Staff File  
**Total Tabs:** 27  
**Service Account:** `user-408@ps-vibe-sales-tele-bot.iam.gserviceaccount.com`

---

## 1. Summary

| Metric | Count |
|--------|-------|
| Total tabs in sheet | 27 |
| Tabs referenced by bot code | 12 |
| Tabs NOT referenced by bot (manual/accounting) | 15 |
| **Mismatches found** | **5 (2 minor, 3 noteworthy)** |

---

## 2. Bot-Referenced Worksheets — Full Verification

### 2.1 `Sales_Daily` ✅ MATCH

| Property | Code (line 209) | Actual Sheet |
|----------|-----------------|--------------|
| Tab name | `Sales_Daily` | `Sales_Daily` ✅ |
| Cols | — | 18 |
| Headers | Date, Voucher No, Member ID, Console ID, Play Mins, Game Amount, Food Amount, Discount, Net Payable, Kpay, Cash, Check Balance, Food Stock Check, Wallet Deduct Mins, Staff, Wave Money, CB Pay, AYA Pay |

**Column references from code**: All `sales_sh.append_row(...)` writes — need runtime verification of column alignment. Headers look correct for a POS-style sales log.

---

### 2.2 `Setting` ✅ MATCH — multi-section config sheet

| Property | Code (line 210) | Actual Sheet |
|----------|-----------------|--------------|
| Tab name | `Setting` | `Setting` ✅ |
| Cols | — | 25 visible headers |

**Column cross-check:**

| Code Reference | Col | Expected | Actual Header | Status |
|---------------|-----|----------|---------------|--------|
| `col_values(8)` | H | Console ID | `Console ID` | ✅ |
| `col_values(9)` | I | Type | `Type` | ✅ |
| `col_values(10)` | J | Multiplier | `Multiplier` | ✅ |
| `col_values(19)` | S | Staff Names | `Staff Names` | ✅ |
| `col_values(20)` | T | Base Salary | `Base Salary` | ✅ |
| `col_values(4)` | D | Food Name | `Food Name` | ✅ |
| `col_values(5)` | E | Selling Price | `Selling Price` | ✅ |
| `col_values(6)` | F | Cost Price | `Cost Price` | ✅ |
| `cell(2,2)` | B2 | 1hr base price | `10,000` | ✅ |
| `cell(3,13)` | M3 | Master threshold | `300,000` (row 3, col M) | ✅ |
| `cell(4,13)` | M4 | Immortal threshold | `1,000,000` (row 4, col M) | ✅ |
| `cell(30,2)` | B30 | Allowed Staff IDs | (not in sample — row 30) | ⚠️ needs check |
| `get("O2:R5")` | O-R | Tier pricing table | O=Top-up Amt, P=Warrior, Q=Master, R=Immortal | ✅ |
| `update("S2:T3")` | S-T | Default staff seed | Staff Names, Base Salary | ✅ |

**Sample row (row 2):** `['1 hr Base', '10,000', '', 'Coca - Cola', '2,500', '0', '', 'C - 01', 'PS5', '1', '', 'Warrior', '0', '', '30,000', '15', '20', '25', 'Thida', '400,000', 'PS VIBE Admin', '@psvibeofficial', 'PS VIBE Admin', '', 'KPay']`

---

### 2.3 `Card_Wallet` ⚠️ MISMATCH — duplicate/misaligned columns

| Property | Code (line 211) | Actual Sheet |
|----------|-----------------|--------------|
| Tab name | `Card_Wallet` (aliased `member_sh`) | `Card_Wallet` ✅ |
| Cols | — | 18 |

**Headers:** `No, Member ID, Customer Name, Phone Number, Lifetime Spend, Ranking Progress, Current Tier, Balance Mins, Total Bought Mins, Total Used Mins, Reg_Staff, (empty), (empty), Referral_Code, (empty), Birthday, Referral_Code, Streak_Count`

**⚠️ Issue #1 — Duplicate "Referral_Code" columns:**
- Column N (14) has header `Referral_Code`  
- Column Q (17) also has header `Referral_Code`
- Code writes to column 17 (`member_sh.update_cell(1, 17, "Referral_Code")`) and reads `A:Q` (17 cols)
- The two columns may have diverged. Verify which one holds actual referral codes.

**⚠️ Issue #2 — Hidden effective_rate column:**
- Column L (12) has **no header label** (empty string)
- Code writes effective_rate to col L: `member_sh.update_cell(i, 12, round(new_rate, 4))`
- Code reads `A:L` for this data
- This is intentional (unlabeled column) but fragile — inserting/deleting columns would silently break it.

**Column reference cross-check:**

| Code Reference | Col | Expected | Actual Header | Status |
|---------------|-----|----------|---------------|--------|
| `col_values(2)` | B | Member ID | `Member ID` | ✅ |
| `get("A:Q")` | A-Q | 17 cols | A-Q (No through 2nd Referral_Code) | ⚠️ see #1 |
| `get("A:H")` | A-H | 8 cols for balance | No through Balance Mins | ✅ |
| `get("A:L")` | A-L | 12 cols for rates | No through (empty col L) | ⚠️ see #2 |
| `cell(1,11)` | K1 | Reg_Staff header | `Reg_Staff` | ✅ |
| `update_cell(1,17)` | Q1 | Referral_Code header | `Referral_Code` (but N also has it) | ⚠️ see #1 |

---

### 2.4 `Stock_Out` ✅ MATCH

| Property | Code (line 212) | Actual Sheet |
|----------|-----------------|--------------|
| Tab name | `Stock_Out` (aliased `stock_sh`) | `Stock_Out` ✅ |
| Cols | — | 8 |
| Headers | Date, Voucher No, Item Name, Qty Out, Unit Price, Total Item Value, Cost Price, Total COGS |

No data rows in sample range. Headers match standard stock-out tracking.

---

### 2.5 `Stock_In` ✅ MATCH

| Property | Code (line 213) | Actual Sheet |
|----------|-----------------|--------------|
| Tab name | `Stock_In` (aliased `stock_in_sh`) | `Stock_In` ✅ |
| Cols | — | 8 |
| Headers | Date, Item Name, Qty In, Unit Cost, Total Cost, Payment, Supplier/Remark, Remaining Qty |

No data rows in sample range. Headers match standard purchase/stock-in tracking.

---

### 2.6 `TopUp_Log` ✅ MATCH

| Property | Code (line 214) | Actual Sheet |
|----------|-----------------|--------------|
| Tab name | `TopUp_Log` (aliased `topup_sh`) | `TopUp_Log` ✅ |
| Cols | — | 13 |
| Headers | Date, Member ID, Current Tier, Customer Name, Top Up Amount, Kpay Amount, Cash Amount, Added Mins, Status, Staff, Wave Money, CB Pay, AYA Pay |

Sample shows gift-based new member topups with 600 mins each. Headers look correct.

---

### 2.7 `Inventory` ✅ MATCH

| Property | Code (line 215) | Actual Sheet |
|----------|-----------------|--------------|
| Tab name | `Inventory` (aliased `inv_sh`) | `Inventory` ✅ |
| Cols | — | 12 |
| Headers | Item Name, Total In (Qty), Total In (Value), Avg Cost Price, Total Out (Qty), Current Stock, Inventory Value, Status, (empty), Total Inventory Value, 13,800, 5/23/2026 14:08 |

⚠️ **Minor:** Columns J-K (`Total Inventory Value`, `13,800`) and column L (`5/23/2026 14:08`) appear to be summary/formula cells in the header row, not actual column headers. This is cosmetic — the bot only writes to A-H via `next_write_row`.

---

### 2.8 `Attendance_Log` ⚠️ MINOR — column count mismatch

| Property | Code (line 309-311) | Actual Sheet |
|----------|---------------------|--------------|
| Tab name | `Attendance_Log` | `Attendance_Log` ✅ |
| Cols | Code creates with **6** | **5** |
| Headers | Month, Staff, Leave_Days, Late_Count, Late_Deduct_Ks |

**Issue #3:** Code creates this tab with `cols=6`, but the actual sheet has only 5 columns of headers. Since the tab already exists (not created by the bot's `add_worksheet` code path), this has no runtime impact — but if the bot ever re-creates it, it'll have an extra empty column.

---

### 2.9 `Console_Booking` ✅ MATCH

| Property | Code (line 322-324) | Actual Sheet |
|----------|---------------------|--------------|
| Tab name | `Console_Booking` | `Console_Booking` ✅ |
| Cols | Code: 9 | Actual: 9 ✅ |
| Headers | BookingID, Date, ConsoleID, MemberID, StartTime, EndTime, Status, Staff, Notes |

Column count matches exactly. Sample shows a completed booking: `BK-20260525-C10-1900`.

---

### 2.10 `Salary_Advance` ✅ MATCH

| Property | Code (line 427-429) | Actual Sheet |
|----------|---------------------|--------------|
| Tab name | `Salary_Advance` | `Salary_Advance` ✅ |
| Cols | Code: 5 | Actual: 5 ✅ |
| Headers | Date, Staff, Amount, Payment, Note |

Perfect match. No data rows in sample range.

---

### 2.11 `Game_Library` ✅ MATCH

| Property | Code (line 440) | Actual Sheet |
|----------|-----------------|--------------|
| Tab name | `Game_Library` | `Game_Library` ✅ |
| Cols | — | 21 |
| Headers | No, Game Name, Final Status, Available Discs, In Use, C-01 through C-10, T7, SD1, SD2, Free Consoles, Installed_On, Genre_Meta |

Code reads with `wb.worksheet("Game_Library")` on line 741. Headers match a game-per-console tracking layout. Sample shows games with TRUE/FALSE flags per console column.

---

### 2.12 `Console_Games` ✅ MATCH

| Property | Code (line 518-520) | Actual Sheet |
|----------|---------------------|--------------|
| Tab name | `Console_Games` | `Console_Games` ✅ |
| Cols | Code: 5 | Actual: 5 ✅ |
| Headers | Console_ID, Game_Title, Install_Type, Date, Notes |

Perfect column count match. Sample data shows per-console game installs.

---

## 3. Unreferenced Tabs (Manual / Accounting)

These 15 tabs exist in the sheet but are **not referenced anywhere** in the bot code (`bot/__init__.py`). They appear to be manual accounting/finance tabs:

| # | Tab Name | Cols | Headers (first few) |
|---|----------|------|---------------------|
| 1 | `Dashboard` | 6 | Console ID, Status, Current Game, Start Time, Play Plan, Expected End Time |
| 2 | `Salary_Payroll` | 10 | Title/header row (report-style, not data table) |
| 3 | `Receipts` | 2 | Voucher ID, JSON blob |
| 4 | `Capital_Setup` | 4 | Shareholder, Role, Capital, Ownership % |
| 5 | `Assets_Register` | 13 | Name, Category, Purchase Date, Cost, Useful Life, etc. |
| 6 | `OPEX_Log` | 8 | Date, Category, Description, Amount, Account, Payment Type, Ref, Notes |
| 7 | `Accounts` | 4 | Account Name, Type, Opening Balance, Notes |
| 8 | `Account_Transfers` | 6 | Date, From, To, Amount, Notes, Reference |
| 9 | `Payables` | 9 | Date, Vendor, Description, Amount, Due Date, Status, etc. |
| 10 | `Receivables` | 9 | Date, Customer, Description, Amount, Due Date, Status, etc. |
| 11 | `Advance_Staff` | 6 | Date, Staff Name, Amount, Payment Type, Notes, Deducted |
| 12 | `Prepaid_Expenses` | 10 | Description, Category, Total Paid, Start/End Date, etc. |
| 13 | `Advance_Payments` | 8 | Date, Party, Description, Amount, Account, Expected Date, Status, Notes |
| 14 | `Promotions` | 14 | ID, Title, Description, Type, Emoji, Discount%, Valid_Until, etc. |
| 15 | `Promotions_Log` | 10 | Date, Voucher_No, Promo_ID, Promo_Title, Member_ID, etc. |

⚠️ **Noteworthy:** `Promotions` and `Promotions_Log` exist but are **not read by the bot**. The bot does not appear to check active promotions or log them. If promo discounts are intended to be automatic, this is a gap.

⚠️ **Noteworthy:** `Salary_Payroll` is a report-style tab (not a data table) — the bot doesn't read or write it.

---

## 4. Missing References

| Search Term | Found in Code? | Notes |
|-------------|---------------|-------|
| `staff_sh` | ❌ NOT FOUND | Staff data lives in `setting_sh` columns S-T (Staff Names, Base Salary). No separate staff sheet. |
| `match_sh` | ❌ NOT FOUND | No match-related worksheet reference exists. |
| `sh.worksheet(` (direct call) | 12 unique calls | All verified above |

---

## 5. Risk Assessment

| Severity | Issue | Impact |
|----------|-------|--------|
| 🟡 Medium | **Duplicate `Referral_Code` in Card_Wallet** (cols N & Q) | Two columns with same header. Code writes to Q but data may be in N. Could cause stale/mismatched referral codes. |
| 🟡 Medium | **Hidden effective_rate column** (Card_Wallet col L) | Unlabeled column. Insert/delete column operations would silently shift data. No header to verify identity. |
| 🟢 Low | **Attendance_Log column count** (5 vs 6) | No runtime impact since tab pre-exists. Only relevant if recreated. |
| 🟢 Low | **Promotions not read by bot** | Promo discounts appear manual-only. Bot won't auto-apply promos. May be intentional. |
| 🟢 Low | **Inventory header row has formula cells** (cols J-L) | Cosmetic. Bot writes to A-H only. |

---

## 6. Recommendations

1. **Resolve dual Referral_Code columns (Card_Wallet):** Decide whether col N (14) or col Q (17) is authoritative. If Q is the canonical one, clear or rename col N. If N is canonical, update code from `update_cell(1, 17, ...)` to `update_cell(1, 14, ...)`.

2. **Label Card_Wallet col L:** Add a header `Effective_Rate` or `Rate` to column L to prevent silent breakage if columns shift.

3. **Consider bot-driven promotions:** If promo discounts should be automatic, the bot needs to read `Promotions` tab and apply active discounts during sales.

4. **Audit `Setting` row 30 (B30):** Code reads `setting_sh.cell(30, 2)` for "Allowed Staff IDs" — verify this cell actually contains the expected data, as it's beyond the first 4 sample rows.

---

*Report generated by automated tab inspection via gspread + service account.*
