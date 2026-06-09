# Sales Bot — Finance & Staff Flow Trace

## FINANCE MODULE (handlers/finance.py)

### Worksheets Used (direct gspread — NO API)
| Sheet Tab | getter Function | Purpose |
|---|---|---|
| OPEX_Log | `get_opex_sh()` | Operating expenses |
| Assets_Register | `get_assets_sh()` | Fixed assets & depreciation |
| Prepaid_Expenses | `get_prepaid_fin_sh()` | Prepaid expenses |
| Account_Transfers | `get_acct_trf_sh()` | Account-to-account transfers |
| Payables | `get_payables_sh()` | Accounts payable |
| Receivables | `get_receivables_sh()` | Accounts receivable |
| Advance_Payments | `get_advpay_sh()` | Advanced payments |

### Finance Entry Point
- **BTN_FINANCIAL_REPORT** → `show_finance_menu()` → keyboard with 12 sub-menus
- Also accessible via `BTN_FINANCE` and `step_finance_menu()`
- All finance writes go DIRECTLY to gspread (no API)

### OPEX Flow (6 states: 101–106)
```
FINANCE_MENU → OPEX_CAT(101) → OPEX_DESC(102) → OPEX_AMT(103) → OPEX_ACCT(104) → OPEX_PAY(105) → OPEX_CONFIRM(106)
```
| State | Handler | Sheet | Columns |
|---|---|---|---|
| FINANCE_MENU | `show_finance_menu()` / `step_finance_menu()` | None (keyboard) | — |
| OPEX_CAT | `prompt_opex_cat()` / `step_opex_cat()` | OPEX_Log | A (Category) |
| OPEX_DESC | `step_opex_desc()` | OPEX_Log | B (Description) |
| OPEX_AMT | `step_opex_amt()` | OPEX_Log | C (Amount) |
| OPEX_ACCT | `step_opex_acct()` | OPEX_Log | D (Account) |
| OPEX_PAY | `step_opex_pay()` | OPEX_Log | E (Payment Method) |
| OPEX_CONFIRM | `step_opex_confirm()` | OPEX_Log | F–H (Date, Notes) → append row |

### Asset Acquisition Flow (8 states: 107–115)
```
FINANCE_MENU → ASSET_NAME(107) → ASSET_CAT(108) → ASSET_DATE(109) → ASSET_COST(110)
→ ASSET_QTY(111) → ASSET_LIFE(112) → ASSET_SALVAGE(113) → ASSET_PAY(114) → ASSET_CONFIRM(115)
```
| State | Handler | Sheet | Notes |
|---|---|---|---|
| ASSET_NAME | `prompt_asset_name()` / `step_asset_name()` | Assets_Register | Name |
| ASSET_CAT | `step_asset_cat()` | Assets_Register | Category |
| ASSET_DATE | `step_asset_date()` | Assets_Register | Acquisition date |
| ASSET_COST | `step_asset_cost()` | Assets_Register | Cost per unit |
| ASSET_QTY | `step_asset_qty()` | Assets_Register | Quantity |
| ASSET_LIFE | `step_asset_life()` | Assets_Register | Useful life (months) |
| ASSET_SALVAGE | `step_asset_salvage()` | Assets_Register | Salvage value |
| ASSET_PAY | `step_asset_pay()` | Assets_register | Payment method |
| ASSET_CONFIRM | `step_asset_confirm()` | Assets_Register | Append row, calc NBV |

### Asset Disposal Flow (5 states: 116–120)
```
ASSET_MENU → ASSET_DISPOSE_SEL(116) → ASSET_DISPOSE_DATE(117) → ASSET_DISPOSE_QTY(118)
→ ASSET_DISPOSE_PROCEEDS(119) → ASSET_DISPOSE_CONFIRM(120)
```
| State | Handler | Sheet | Notes |
|---|---|---|---|
| ASSET_DISPOSE_SEL | `prompt_asset_dispose_sel()` / `step_asset_dispose_sel()` | Assets_Register | Select asset to dispose |
| ASSET_DISPOSE_DATE | `step_asset_dispose_date()` | Assets_Register | Disposal date |
| ASSET_DISPOSE_QTY | `step_asset_dispose_qty()` | Assets_Register | Qty disposed |
| ASSET_DISPOSE_PROCEEDS | `step_asset_dispose_proceeds()` | Assets_Register | Sale proceeds |
| ASSET_DISPOSE_CONFIRM | `step_asset_dispose_confirm()` | Assets_Register | Update asset status |

### Prepaid Flow (6 states: 121–127)
```
FINANCE_MENU → PREPAID_DESC(121) → PREPAID_CAT(122) → PREPAID_AMT(123)
→ PREPAID_ACCT(124) → PREPAID_START(125) → PREPAID_END(126) → PREPAID_CONFIRM(127)
```
| State | Handler | Sheet | Notes |
|---|---|---|---|
| PREPAID_DESC | `prompt_prepaid_desc()` / `step_prepaid_desc()` | Prepaid_Expenses | Description |
| PREPAID_CAT | `step_prepaid_cat()` | Prepaid_Expenses | Category |
| PREPAID_AMT | `step_prepaid_amt()` | Prepaid_Expenses | Amount |
| PREPAID_ACCT | `step_prepaid_acct()` | Prepaid_Expenses | Account |
| PREPAID_START | `step_prepaid_start()` | Prepaid_Expenses | Start date |
| PREPAID_END | `step_prepaid_end()` | Prepaid_Expenses | End date (auto-compute) |
| PREPAID_CONFIRM | `step_prepaid_confirm()` | Prepaid_Expenses | Append row |

### Account Transfer Flow (5 states: 128–132)
| State | Handler | Sheet | Notes |
|---|---|---|---|
| ACCT_TRF_FROM | prompt/step | Account_Transfers | Source account |
| ACCT_TRF_TO | step_acct_trf_to | Account_Transfers | Destination account |
| ACCT_TRF_AMT | step_acct_trf_amt | Account_Transfers | Amount |
| ACCT_TRF_NOTE | step_acct_trf_note | Account_Transfers | Note |
| ACCT_TRF_CONFIRM | step_acct_trf_confirm | Account_Transfers | Append row |

### Payables / Receivables Flows (5 states each: 133–144)
**PAY_FLOW:** PAY_VENDOR → PAY_DESC → PAY_AMT → PAY_DUE → PAY_ACCT → PAY_CONFIRM
- Sheet: Payables
- Handlers: `prompt_pay_vendor()` / `step_pay_*`

**REC_FLOW:** REC_CUST → REC_DESC → REC_AMT → REC_DUE → REC_ACCT → REC_CONFIRM
- Sheet: Receivables
- Handlers: `prompt_rec_cust()` / `step_rec_*`

### Reports (FIN_REPORT_MENU = 145)
| State | Handler | Sheet |
|---|---|---|
| FIN_REPORT_MENU | `step_fin_report_menu()` | Inline keyboard → P&L / BS / ACCTS |

### Capital Contribution & Shareholder Equity (shareholder flow)
SHARE_NAME → SHARE_ROLE → SHARE_CAP → SHARE_OWN → SHARE_CONFIRM (states 146–153)
- Handlers: `show_shareholder_menu()` / `step_shareholder_menu()` / `step_cap_*()` / `step_share_*()`
- Sheet: **Capital_Setup** (columns: A=Shareholder, B=Role, C=Capital, D=Ownership%)
- Actually all capital+shareholder data stored in a single **Capital_Setup** sheet

### Settlement Flows (3 states each: 154–159)
**PAY_SETTLE:** PAY_SETTLE_LIST → PAY_SETTLE_ACCT → PAY_SETTLE_CONFIRM
- Sheet: Payables
- Handlers: `prompt_pay_settle_*()` → `step_pay_settle_*()`

**REC_SETTLE:** REC_SETTLE_LIST → REC_SETTLE_ACCT → REC_SETTLE_CONFIRM
- Sheet: Receivables

### Advance Payment Flow (7 states: 160–168)
ADVPAY_PARTY → ADVPAY_DESC → ADVPAY_AMT → ADVPAY_ACCT → ADVPAY_DUE → ADVPAY_NOTE → ADVPAY_CONFIRM → ADVPAY_LIST → ADVPAY_SETTLE_CONFIRM
- Sheet: Advance_Payments
- Handlers: `prompt_advpay_*()` / `step_advpay_*()`

---

## ATTENDANCE MODULE (handlers/attendance.py)

### Flow: ATTEND_STAFF(37) → ATTEND_LEAVE(38) → ATTEND_LATE(39) → ATTEND_DEDUCT(40)
| State | Handler | Sheet |
|---|---|---|
| ATTEND_STAFF | `cmd_setattend()` / `step_attend_staff()` | Attendance (via `get_attendance_sh()` in __init__) |
| ATTEND_LEAVE | `step_attend_leave()` | Attendance (leave column) |
| ATTEND_LATE | `step_attend_late()` | Attendance (late column) |
| ATTEND_DEDUCT | `step_attend_deduct()` | Attendance (deduction column) |
| _helper | `_attend_save_and_next()` | Writes to Attendance sheet |
| _finish | `_attend_finish()` | Final save + summary |

- **Bypasses API:** `save_attendance()` in __init__ exists but attendance module writes directly via `get_attendance_sh()` → gspread

---

## PAYROLL MODULE (handlers/payroll.py)

| Function | Type | Description |
|---|---|---|
| `calc_monthly_payroll(month_str)` | def | Calculates all staff salaries from Attendance sheet |
| `cmd_payroll()` | async def | Shows payroll summary |
| `cmd_payroll_cmd()` | async def | /payroll command |
| `cmd_kpi_cmd()` | async def | Staff KPI command |

- Sheet used: **Salary_Advance**, **Attendance**, **Staff** (via `fetch_staff`, `fetch_base_salaries`)
- **Bypasses API:** Direct gspread calculations, no API call

---

## SALARY ADVANCE MODULE (handlers/salary_adv.py)

### Flow: SAL_ADV_STAFF(44) → SAL_ADV_AMT(45) → SAL_ADV_PAY(46) → SAL_ADV_CONFIRM(47)
| State | Handler | Sheet |
|---|---|---|
| SAL_ADV_STAFF | `step_sal_adv_staff()` | Salary_Advance (A=Date, B=Staff) |
| SAL_ADV_AMT | `step_sal_adv_amt()` | Salary_Advance (C=Amount) |
| SAL_ADV_PAY | `step_sal_adv_pay()` | Salary_Advance (D=Payment) |
| SAL_ADV_CONFIRM | `step_sal_adv_confirm()` | Salary_Advance (E=Note → append row) |

---

## DISCOUNT/PROMO MODULE (handlers/discount.py)

| State | Handler | Sheet |
|---|---|---|
| DISCOUNT (entry) | `prompt_discount()` | Sales_Daily (via daily sales) |
| PROMO_SELECT(169) | `prompt_promo_select()` / `step_promo_select()` | Promotions_Log |
| BUNDLE_FOC | `step_bundle_foc()` | Promotions_Log |
| (Numeric) | `step_discount()` | Sales_Daily |

- **Bypasses API:** Direct gspread, modifies Sales_Daily row in-place

---

## REFERRAL MODULE (handlers/referral.py)

| State | Handler | Sheet |
|---|---|---|
| REFERRAL_CODE(171) | `prompt_referral_code()` / `step_referral_code()` | Referral_Code |

---

## KEY FINDINGS

### 1. 🔴 ALL Finance/Staff handlers bypass API
**Zero API calls** in any finance, attendance, payroll, salary advance, discount, or referral handler. They all write directly to gspread via sheet getter functions.

| Sheet | Accessed By | Via API? |
|---|---|---|
| OPEX_Log | `get_opex_sh()` | ❌ Direct gspread |
| Assets_Register | `get_assets_sh()` | ❌ Direct gspread |
| Prepaid_Expenses | `get_prepaid_fin_sh()` | ❌ Direct gspread |
| Account_Transfers | `get_acct_trf_sh()` | ❌ Direct gspread |
| Payables | `get_payables_sh()` | ❌ Direct gspread |
| Receivables | `get_receivables_sh()` | ❌ Direct gspread |
| Advance_Payments | `get_advpay_sh()` | ❌ Direct gspread |
| Attendance | `get_attendance_sh()` | ❌ Direct gspread |
| Salary_Advance | `get_salary_adv_sh()` | ❌ Direct gspread |
| Capital_Accounts | (direct) | ❌ Direct gspread |
| Shareholders_Equity | (direct) | ❌ Direct gspread |
| Promotions_Log | `get_promo_log_sh()` | ❌ Direct gspread |

These are **ADDITIONAL sheets** beyond the standard 12 verified earlier:
- OPEX_Log ✅
- Assets_Register ✅
- Prepaid_Expenses ✅
- Account_Transfers ✅
- Payables ✅
- Receivables ✅
- Advance_Payments ✅
- Attendance_Log ✅ (code refs `Attendance` but actually uses `Attendance_Log`)
- Salary_Advance ✅
- Capital_Setup ✅ (not `Capital_Accounts`/`Shareholders_Equity`)
- Promotions ✅
- Promotions_Log ✅

### 3. State count: ~50+ total finance/staff states
- 12 FINANCE states (menu + sub-menus)
- 6 OPEX states
- 10 Asset states (5 acquisition + 5 disposal)
- 7 Prepaid states
- 5 Account Transfer states
- 6 Payables states
- 6 Receivables states
- 3 Capital states
- 5 Shareholder states
- 3 Pay Settlement states
- 3 Rec Settlement states
- 8 Advance Payment states
- 4 Attendance states
- 4 Salary Advance states
- 2 Discount/Promo + 1 Referral
- **~85 total states in finance+staff domain**
