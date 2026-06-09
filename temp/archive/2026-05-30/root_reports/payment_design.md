# Payment Breakdown System — Design Document

## 1. Current State Analysis

### Sheets Structure

| Sheet | Current Payment Columns | Need |
|-------|------------------------|------|
| **Sales_Daily** (A:O) | J=Kpay, K=Cash | + Wave Money, CB Pay, AYA Pay |
| **TopUp_Log** (A:I) | F=KpayAmount, G=CashAmount | + Other methods |
| **Stock_In** (A:F) | F=Payment (free-text) | Needs standardization |
| **Salary_Advance** (A:E) | D=Payment (free-text) | Needs standardization |
| **Setting!Y:Y** | KPay, Cash, Wave Money, CB Pay, AYA Pay | Source of truth |

### Payment Methods in Code

```python
# main.py line 3871
FINANCE_ACCOUNTS = ["Cash Box", "KBZ Bank", "MMQR", "AYA Bank"]

# main.py line 4060
_pay_map = {
    "Cash Box": "Cash", 
    "MMQR": "KPay", 
    "KBZ Bank": "Bank Transfer", 
    "AYA Bank": "Bank Transfer"
}

# main.py line 249 — Salary_Advance column D header
"Payment (Cash/KPay)"
```

### Code Flows Using Payments

| Flow | Lines | Current Method |
|------|-------|----------------|
| New Member | 1939-2204 | KPay amount input, remainder = Cash |
| Top Up | 2361-2541 | KPay amount input, remainder = Cash |
| Stock In | 563-811 | Cash + KPay split (SI_PAY_SPLIT) |
| Finance OPEX | 4061 | Account-based (Cash Box, KBZ, MMQR, AYA) |
| API Receipts | api_server.js:328-355 | KPay + Cash only |

---

## 2. Proposed Sales_Daily Column Layout

### Approach A: Simple (Add 3 Columns) ✅ RECOMMENDED

Append columns after existing Cash (K):

```
Current: A B C D E F G H I J K L M N O
         ...                     Kpay Cash ...
         
New:     A B C D E F G H I J K  L  M  N  O  P  Q  R
         ...                     Kpay Cash Wave CB  AYA Chk* Food* Wallet Staff
                                                       Bal  Stock Deduct
```

**New layout (J onward):**
```
J = Kpay
K = Cash
L = Wave Money
M = CB Pay
N = AYA Pay
O = Check Balance
P = Food Stock Check
Q = Wallet Deduct Mins
R = Staff
```

**Why:** Minimal column shift. Existing data intact. Simple to implement.

### Approach B: Normalized (Single Payment JSON Column)

```
J = Payment_JSON  →  {"KPay": 5000, "Cash": 3000, "Wave": 2000}
K = Net Payable
L = Check Balance
...
```

**Why:** Flexible, no column limit, easy to extend.
**Why NOT:** Hard to filter/sum in Sheets, loss of per-column SUM formulas.

### Approach C: Dynamic (Read from Setting!Y)

```
J = Payment Method 1 (from Y2)
K = Payment Method 2 (from Y3)
L = Payment Method 3 (from Y4)
... dynamically generated
```

**Why:** Auto-adapts when Y column changes.
**Why NOT:** Complex to maintain, column indices shift dynamically.

---

## 3. TopUp_Log New Layout

```
Current: A=Date B=MemberID C=Tier D=Name E=Amount F=Kpay G=Cash H=Mins I=Status
New:     A=Date B=MemberID C=Tier D=Name E=Amount F=Kpay G=Cash H=Wave I=CBPay J=AYAPay K=Mins L=Status
```

Or **Approach A** for consistency: add Wave (H), CB Pay (I), AYA Pay (J), shift Mins→K, Status→L.

## 4. Stock_In & Salary_Advance

Keep single Payment column but standardize to dropdown from Setting!Y. Add split support:
- Single method: "KPay", "Cash", "Wave Money", "CB Pay", "AYA Pay"
- Split: "KPay(5000)+Cash(3000)" convention (or add dedicated split columns)

---

## 5. Affected Code Sections (All in main.py)

| # | Location | Lines | Change Description |
|---|----------|-------|--------------------|
| 1 | Salary_Advance header | 249, 255 | Update "Cash/KPay" → full list |
| 2 | State constants | 547, 551, 553 | Add WAVE_AMT, CB_AMT, AYA_AMT states |
| 3 | Stock In payment split | 572-573 | Generalize SI_PAY_SPLIT to multi-method |
| 4 | BTN_SI_SPLIT label | 687 | Update button text |
| 5 | New Member KPay step | 1939-2110 | Replace KPay-only with multi-method selector |
| 6 | New Member confirm/save | 2135-2204 | Write all method amounts |
| 7 | Top Up KPay step | 2361-2461 | Replace KPay-only with multi-method selector |
| 8 | Top Up confirm/save | 2489-2541 | Write all method amounts |
| 9 | FINANCE_ACCOUNTS | 3871 | Align with Setting!Y |
| 10 | _pay_map | 4060 | Update mapping |
| 11 | Sales_Daily write | Spread across file | Add new columns |
| 12 | TopUp_Log write | Spread across file | Add new columns |
| 13 | API server receipts | api_server.js:328-355 | Dynamic payment method rows |

## 6. Data Migration Plan

1. **Sales_Daily**: Add columns L, M, N (fill existing rows with 0)
2. **TopUp_Log**: Add columns H, I, J (fill existing rows with 0)
3. **Stock_In**: No migration needed (free-text column)
4. **Salary_Advance**: No migration needed
5. Update **Setting!Y** dropdown validation for all affected sheets

## 7. Implementation Estimate

| Metric | Value |
|--------|-------|
| Files changed | 3 (main.py, api_server.js, customer_bot.py) |
| Lines added (main.py) | ~150-200 |
| Lines added (api_server.js) | ~30-50 |
| Lines added (customer_bot.py) | ~50-80 |
| New states | 6-9 (WAVE_AMT, CB_AMT, AYA_AMT, etc.) |
| New functions | 2-3 (payment_method_selector, payment_breakdown_display) |
| Risk level | Medium (payment is core flow, careful testing needed) |

## 8. Recommendation

**Approach A (Simple + 3 columns)** for Sales_Daily and TopUp_Log.
- ✅ Backward compatible
- ✅ Easy to sum per-column in Sheets
- ✅ Minimal code changes
- ✅ Supports all 5 payment methods
- ❌ Hardcoded — if new method added, need code+sheet update

The real value-add is the **bot UI** — replacing the current "KPay amount (remainder=Cash)" with a proper multi-method payment breakdown selector where staff can split across any combination of the 5 methods.
