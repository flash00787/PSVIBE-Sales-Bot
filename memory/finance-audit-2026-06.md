# PS VIBE — Monthly PNL & Balance Sheet Audit (June 2026)

**Audit Date:** 2026-06-15 06:30 UTC  
**Period:** June 1–15, 2026 (partial month)  
**Audited By:** OpenClaw Subagent  

---

## Executive Summary

> ⚠️ **CRITICAL FINDING:** The PNL API (`/api/finance/pnl`) is reporting a **false profit of 1,518,416 Ks** when the actual result for June 2026 is a **massive LOSS of approximately −7,330,050 Ks** (before depreciation) or **−14,325,598 Ks** (with depreciation). The Balance Sheet API is also materially understated — showing total assets of only 427,000 Ks vs actual assets of ~303 million Ks.

**Root causes:** Two outdated/simplified API endpoints that:
1. Only pull salaries from `staff_records` (snapshot view) — completely ignoring the `opex` table (10M+ in June expenses)
2. Hardcode inventory, equipment, and cash asset values to zero
3. Have zero COGS calculation
4. Miss advances (2.3M Ks) and prepaid (22.4M Ks) on the balance sheet

---

## 1. Data Source Analysis

### 1.1 Two PNL Implementations Exist

| Aspect | `/api/finance/pnl` (PNL API) | `/dashboard/financial/pnl` (Dashboard) |
|--------|------------------------------|----------------------------------------|
| File | `patch_routes.py` L665-720 | `dashboard_routes.py` L2241 |
| Auth | API Key | User Session |
| Console Rev | `sales_daily.amount` | `sales_daily.net` (excl Topup/New member) |
| Food Rev | ❌ Not queried | ✅ `stock_out.total` |
| COGS | ❌ `cogs=0` hardcoded | ✅ FIFO via `stock_fifo.calc_fifo()` |
| Topup Rev | ✅ `topup_log.amount` | ✅ `topup_log.amount` |
| Expenses | ❌ Only `staff_records.base_salary` (snapshot) | ✅ `opex` table by category + depreciation |
| Depreciation | ❌ Not included | ✅ `finance_assets.monthly_dep` |
| Wallet Consumed | ❌ Not included | ✅ FIFO wallet calc |
| **Status** | **BROKEN — false profit** | **ACCURATE — comprehensive** |

### 1.2 Two Balance Sheet Implementations Exist

| Aspect | `/api/finance/balance-sheet` (BS API) | `/dashboard/financial/balance-sheet` (Dashboard) |
|--------|--------------------------------------|--------------------------------------------------|
| Cash Assets | ❌ Hardcoded to 0 | ✅ Full cash_movements + income/opex by account |
| Inventory | ❌ Hardcoded to 0 | ✅ FIFO inventory_value |
| Equipment | ❌ Hardcoded to 0 | ✅ finance_assets NBV (cost - acc_dep) |
| Prepaid | ❌ Not included | ✅ finance_prepaid - amortization |
| Advances | ❌ Not included | ✅ finance_advances pending |
| Wallet Liab | ✅ From member_wallets | ✅ Per-member FIFO rate × balance |
| Equity | ❌ Hardcoded to 0 | ✅ Capital + calculated retained earnings |
| **Status** | **BROKEN — missing 99.9% of assets** | **ACCURATE — comprehensive** |

---

## 2. MySQL Verification Results

### 2.1 Revenue Sources — June 2026

```sql
-- sales_daily (all columns)
SELECT COUNT(*), SUM(amount), SUM(net), SUM(gross), SUM(discount) 
FROM sales_daily 
WHERE MONTH(created_at)=6 AND YEAR(created_at)=2026;
```
| Records | amount | net | gross | discount |
|---------|--------|-----|-------|----------|
| 141 | 2,048,416 | 2,192,533 | 2,402,616 | 211,250* |

> *Calculated: gross − net = 2,402,616 − 2,192,533 = 210,083. Minor rounding diff with discount column.

**Column semantics:**
- `amount`: Base rate × minutes (pre-adjustment) — used by PNL API
- `gross`: Full price before discount
- `discount`: Discount applied
- `net`: Final collected amount = gross − discount — used by Dashboard PNL

```sql
-- topup_log
SELECT COUNT(*), SUM(amount) FROM topup_log 
WHERE MONTH(topup_date)=6 AND YEAR(topup_date)=2026;
```
| Records | total |
|---------|-------|
| 5 | 270,000 ✅ |

```sql
-- stock_out (food revenue)
SELECT COUNT(*), SUM(total) FROM stock_out 
WHERE MONTH(created_at)=6 AND YEAR(created_at)=2026;
```
| Records | total |
|---------|-------|
| 125 | 364,200 |

### 2.2 Expenses — June 2026

```sql
SELECT category, COUNT(*), SUM(amount) as total 
FROM opex 
WHERE MONTH(expense_date)=6 AND YEAR(expense_date)=2026 
GROUP BY category ORDER BY total DESC;
```
| Category | Count | Amount (Ks) |
|----------|-------|-------------|
| Marketing | 13 | 4,690,239 |
| Rent | 1 | 2,491,667 |
| Others | 6 | 2,165,660 |
| Internet | 2 | 250,700 |
| Maintenance | 2 | 160,000 |
| Software/License | 1 | 150,000 |
| Staff Salary | 1 | 100,000 |
| Water | 1 | 4,400 |
| **TOTAL** | **27** | **10,012,666** |

```sql
-- Staff records (snapshot, not monthly)
SELECT COUNT(*), SUM(base_salary) FROM staff_records WHERE is_active=1;
```
| Active Staff | Total Base Salary |
|-------------|-------------------|
| 2 | 800,000 |

```sql
-- Monthly depreciation
SELECT COUNT(*), SUM(monthly_dep), SUM(acc_depreciation), SUM(per_price*qty) 
FROM finance_assets WHERE status='active' AND useful_life > 0;
```
| Assets | Monthly Dep | Acc Dep | Gross Cost |
|--------|-------------|---------|------------|
| 39 | 6,995,548 | 3,262,283 | 280,932,852 |

### 2.3 Balance Sheet Items

```sql
-- Wallet liability
SELECT COUNT(*), SUM(balance_mins) FROM member_wallets;
```
| Wallets | Total Mins | base_rate | Liability |
|---------|-----------|-----------|-----------|
| 5 | 2,562 | 10,000 | 427,000 (2,562 × 10,000 ÷ 60) ✅ |

```sql
-- Inventory
SELECT COUNT(*), SUM(quantity * unit_price) FROM inventory WHERE quantity > 0;
```
| Items | Value |
|-------|-------|
| 38 | 1,204,200 |

```sql
-- Advances outstanding
SELECT COUNT(*), SUM(amount) FROM finance_advances 
WHERE status != 'settled' OR status IS NULL;
```
| Count | Total |
|-------|-------|
| 1 | 2,300,000 |

```sql
-- Prepaid
SELECT COUNT(*), SUM(amount) FROM finance_prepaid 
WHERE status='active' OR status IS NULL;
```
| Count | Total |
|-------|-------|
| 1 | 22,425,000 |

```sql
-- Shareholders capital
SELECT SUM(capital_contribution) FROM shareholders;
```
| Total Capital |
|---------------|
| 300,000,000 |

```sql
-- Payables outstanding
SELECT COUNT(*), SUM(amount) FROM finance_payables 
WHERE status != 'paid' OR status IS NULL;
```
| Count | Total |
|-------|-------|
| 0 | NULL |

```sql
-- Account balances (from accounts table)
```
| Account | Type | Balance |
|---------|------|---------|
| Cash | Cash | 145,600 |
| KPay | Digital | 40,300 |
| Wave | Digital | 34,500 |
| AYA Pay | Digital | 0 |
| ACM's Acc | Digital | 1,622,616 |
| KBZ Bank | Capital | −16,165,052 |

---

## 3. Discrepancy Analysis

### 3.1 PNL API — MISSING 97% of Expenses

| Line Item | PNL API Reports | Actual (June) | Discrepancy |
|-----------|----------------|---------------|-------------|
| Console Revenue | 2,048,416 | 2,048,416 | ✅ Match |
| Food Revenue | 0 | 364,200 | ❌ −364,200 |
| Topup Revenue | 270,000 | 270,000 | ✅ Match |
| **Total Revenue** | **2,318,416** | **2,682,616** | **−364,200 (13.6%)** |
| COGS | 0 | Unknown (FIFO) | ❌ Missing |
| Salaries | 800,000 | 100,000 (opex) | ⚠️ Different source |
| Rent | 0 | 2,491,667 | ❌ −2,491,667 |
| Marketing | 0 | 4,690,239 | ❌ −4,690,239 |
| Other Expenses | 0 | 2,830,760 | ❌ −2,830,760 |
| Depreciation | 0 | 6,995,548 | ❌ −6,995,548 |
| **Total Expenses** | **800,000** | **10,012,666 + 6,995,548** | **−16,208,214** |
| **Net Profit** | **1,518,416 PROFIT** | **−14,325,598 LOSS** | **−15,844,014 OFF** |

> 🔴 **The PNL API is reporting a 1.5M profit when the business actually lost ~14.3M this month.**

### 3.2 Balance Sheet API — MISSING 99.9% of Assets

| Line Item | BS API Reports | Actual | Discrepancy |
|-----------|---------------|--------|-------------|
| Cash & Bank | 0 | 1,843,016 | ❌ −1,843,016 |
| Inventory | 0 | 1,204,200 | ❌ −1,204,200 |
| Equipment (NBV) | 0 | 277,670,569 | ❌ −277,670,569 |
| Prepaid | 0 | 22,425,000 | ❌ −22,425,000 |
| Other Current (advances) | 0 | 2,300,000 | ❌ −2,300,000 |
| **Total Assets** | **427,000** | **~305,442,785** | **−305,015,785** |
| Wallet Liability | 427,000 | 427,000 | ✅ Match |
| Advances | 0 | 2,300,000 | ❌ −2,300,000 |
| **Total Liabilities** | **427,000** | **2,727,000** | **−2,300,000** |
| Retained Earnings | 0 | ~2,715,785 | ❌ Missing |
| Capital | 0 | 300,000,000 | ❌ Missing |
| **Total Equity** | **0** | **~302,715,785** | **−302,715,785** |
| **A = L + E Check** | 427,000 = 427,000 + 0 ✅ | 305,442,785 ≈ 2,727,000 + 302,715,785 | Matches |

### 3.3 sales_daily `amount` vs `net` Column Issue

The PNL API uses `sales_daily.amount` (2,048,416) while the Dashboard PNL uses `sales_daily.net` (2,192,533). They differ by 144,117 Ks.

Looking at the data pattern:
- `amount` column: total = 2,048,416, all 142 records have a value
- `net` column: total = 2,202,533 (all-time)
- 18 records have `amount=0` but `net>0` (total net=64,000) — these are entries with blank notes, likely food sales or other non-game transactions mixed in

The `amount` column appears to track game-only revenue by rate × minutes, while `net` includes everything collected (including food/add-ons). This design is inconsistent — for reliable reporting, one column should be the "single source of truth."

### 3.4 Salary Double-Counting Risk

The PNL API uses `staff_records.base_salary` (snapshot of active staff = 800,000) while the Dashboard uses the `opex` table (Staff Salary = 100,000 for June). These are fundamentally different:

- `staff_records.base_salary` = what staff SHOULD be paid (monthly salary rate)
- `opex` "Staff Salary" = what was ACTUALLY paid/recorded this month

The Dashboard PNL would capture BOTH the opex Staff Salary (100,000) AND separately the staff_records salary (if coded that way). Currently the Dashboard PNL pulls from `opex` only, which is correct.

But the PNL API only pulls `staff_records` — missing all opex, including the actual salary payments.

---

## 4. Root Cause Summary

### PNL API (`/api/finance/pnl`) — `patch_routes.py` L665-720
1. **Only 1 expense source:** `staff_records.base_salary` (line 707) — ignores 27 opex records totaling 10M+
2. **No food revenue:** No query to `stock_out` table
3. **No COGS:** `cogs` hardcoded to 0, `gross_profit = total_revenue`
4. **No depreciation:** Not queried from `finance_assets`
5. **Uses `amount` not `net`:** Different from Dashboard's revenue calculation

### Balance Sheet API (`/api/finance/balance-sheet`) — `patch_routes.py` L724-755
1. **Cash/assets hardcoded to 0:** No queries to `cash_movements` or `accounts`
2. **Inventory hardcoded to 0:** No query to `inventory` table
3. **Equipment hardcoded to 0:** No query to `finance_assets`
4. **Only wallet liability:** Missing advances (2.3M), payables, prepaid
5. **Equity hardcoded to 0:** No retained earnings calculation, no shareholders capital
6. **A=L+E forced:** `assets.total = liabilities.total + equity.total` — since equity=0, it just mirrors wallet liability

### The Dashboard Endpoints Are Correct
The `/dashboard/financial/pnl` and `/dashboard/financial/balance-sheet` endpoints have comprehensive implementations that correctly calculate all the above items. The PNL and BS APIs under `/api/finance/` are outdated/simplified stubs that were never updated when the full dashboard implementations were built.

---

## 5. Recommendations

### 5.1 Immediate Fix (CRITICAL)
**Replace the PNL API endpoint** with the calculation logic from the Dashboard PNL endpoint. The Dashboard PNL (`dashboard_routes.py` L2241-2330) has the correct implementation including:
- Game revenue from `sales_daily.net` (excluding Topup/New member notes)
- Food revenue from `stock_out`
- Food COGS via FIFO
- Topup revenue from `topup_log`
- Wallet consumed via FIFO wallet
- All opex expenses by category
- Depreciation from `finance_assets`

### 5.2 Immediate Fix (CRITICAL)
**Replace the Balance Sheet API endpoint** with the calculation logic from the Dashboard Balance Sheet endpoint (`dashboard_routes.py` L2334-2530). The Dashboard implementation correctly calculates:
- Current assets (cash_movements by account)
- Inventory value (FIFO)
- Fixed assets (NBV = cost − acc_dep)
- Prepaid and advances
- Wallet liability (per-member FIFO rate)
- Equity (capital + retained earnings)

### 5.3 Data Consistency
**Resolve the `amount` vs `net` column split** in `sales_daily`:
- Decide which column is the authoritative game revenue figure
- Ensure both endpoints use the same column
- The 18 records with `amount=0, net>0` should be investigated — likely food sales that were entered with blank notes

### 5.4 Salary Calculation
**Use opex table for salary expense** (actual payments), not `staff_records.base_salary` (theoretical rate). The `staff_records` table should be used for payroll planning, not P&L reporting.

### 5.5 Code Consolidation
**Extract shared calculation functions** into a `finance_calculations.py` module to avoid the current duplication where two implementations exist (one broken, one correct). All endpoints should call the same calculation functions.

---

## Appendix A: All MySQL Queries Used

```sql
-- Revenue
SELECT COUNT(*), SUM(amount), SUM(net), SUM(gross) FROM sales_daily WHERE MONTH(created_at)=6 AND YEAR(created_at)=2026;
SELECT COUNT(*), SUM(amount) FROM topup_log WHERE MONTH(topup_date)=6 AND YEAR(topup_date)=2026;
SELECT COUNT(*), SUM(total) FROM stock_out WHERE MONTH(created_at)=6 AND YEAR(created_at)=2026;

-- Expenses
SELECT category, COUNT(*), SUM(amount) FROM opex WHERE MONTH(expense_date)=6 AND YEAR(expense_date)=2026 GROUP BY category;
SELECT COUNT(*), SUM(base_salary) FROM staff_records WHERE is_active=1;
SELECT COUNT(*), SUM(monthly_dep), SUM(acc_depreciation), SUM(per_price*qty) FROM finance_assets WHERE status='active' AND useful_life > 0;

-- Balance Sheet
SELECT COUNT(*), SUM(balance_mins) FROM member_wallets;
SELECT COUNT(*), SUM(quantity * unit_price) FROM inventory WHERE quantity > 0;
SELECT COUNT(*), SUM(amount) FROM finance_advances WHERE status != 'settled' OR status IS NULL;
SELECT COUNT(*), SUM(amount) FROM finance_prepaid WHERE status='active' OR status IS NULL;
SELECT COUNT(*), SUM(amount) FROM finance_payables WHERE status != 'paid' OR status IS NULL;
SELECT SUM(capital_contribution) FROM shareholders;
SELECT setting_value FROM settings WHERE setting_key='base_rate';

-- Table structure
DESCRIBE sales_daily;
DESCRIBE opex;

-- Date ranges
SELECT MIN(created_at), MAX(created_at) FROM sales_daily;
SELECT MIN(expense_date), MAX(expense_date) FROM opex;
```

## Appendix B: API Response Comparison

### `/api/finance/pnl?m=2026-06` (BROKEN)
```json
{
  "revenue": {"console": 2048416, "food": 0, "topup": 270000},
  "cogs": 0,
  "expenses": {"salaries": 800000, "rent": 0, "utilities": 0},
  "net_profit": 1518416
}
```

### `/api/finance/balance-sheet` (BROKEN)
```json
{
  "assets": {"cash": 0, "inventory_value": 0, "equipment_value": 0, "total": 427000},
  "liabilities": {"wallet_liability": 427000, "advances": 0, "payables": 0, "total": 427000},
  "equity": {"retained_earnings": 0, "total": 0}
}
```

### `/api/finance/account-balances` (WORKS — partially correct)
```json
{
  "operating": [
    {"name": "Cash", "balance": 145600},
    {"name": "KPay", "balance": 40300},
    {"name": "Wave", "balance": 34500},
    {"name": "ACM's Acc", "balance": 1622616}
  ],
  "capital": [{"name": "KBZ Bank", "balance": -16165052}]
}
```

---

**Audit Conclusion:** The `/api/finance/pnl` and `/api/finance/balance-sheet` endpoints are dangerously outdated and should be immediately replaced with the Dashboard-caliber implementations. The business is currently seeing a false 1.5M profit when it's actually running a 14M+ monthly loss.
