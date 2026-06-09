# Task: Payment-Breakdown-System-Design

## Objective
Design a payment breakdown system for PS Vibe bots that supports multiple payment methods (KPay, Cash, Wave Money, CB Pay, AYA Pay) across all financial sheets, and plan the code changes needed.

## Current State

### Sheet Column Y (Setting — Payment Methods)
```
KPay, Cash, Wave Money, CB Pay, AYA Pay
```

### Current Sheet Structures

**Sales_Daily (A:O):**
```
A=Date, B=VoucherNo, C=MemberID, D=ConsoleID, E=PlayMins, F=GameAmount, 
G=FoodAmount, H=Discount, I=NetPayable, J=Kpay, K=Cash, L=CheckBalance, 
M=FoodStockCheck, N=WalletDeductMins, O=Staff
```
👉 Only Kpay (J) and Cash (K) columns exist

**TopUp_Log (A:I):**
```
A=Date, B=MemberID, C=CurrentTier, D=CustomerName, E=TopUpAmount, 
F=KpayAmount, G=CashAmount, H=AddedMins, I=Status
```
👉 Only Kpay (F) and Cash (G) columns exist

**Stock_In (A:F):**
```
A=Date, B=ItemName, C=QtyIn, D=UnitCost, E=TotalCost, F=Payment
```
👉 Single Payment column (free-text)

**Salary_Advance (A:E):**
```
A=Date, B=Staff, C=Amount, D=Payment, E=Note
```
👉 Single Payment column (free-text)

### Current Code Payment Logic (main.py)
- **FINANCE_ACCOUNTS** (line 3871): `["Cash Box", "KBZ Bank", "MMQR", "AYA Bank"]`
- **_pay_map** (line 4060): `{"Cash Box": "Cash", "MMQR": "KPay", "KBZ Bank": "Bank Transfer", "AYA Bank": "Bank Transfer"}`
- **New Member flow**: Cash + KPay split only (user inputs KPay amount, remainder = Cash)
- **Top Up flow**: Cash + KPay split only
- **Stock In**: Cash + KPay split ("ခွဲပေး (Cash + KPay)")
- **API Server receipts**: KPay & Cash only in HTML templates

## Requirements

1. Design a flexible payment breakdown that works for **Sales_Daily** sheet
2. Support all 5 payment methods: KPay, Cash, Wave Money, CB Pay, AYA Pay
3. Handle split payments (e.g., 50% KPay + 30% Wave + 20% Cash)
4. Must integrate with existing New Member, Top Up, and Stock In flows
5. Receipt templates must show full payment breakdown
6. Consider: sheet column layout, code changes needed, data integrity

## Deliverables
Write to VPS at `/root/.coordination/TASK_payment_design.md`:
1. **Proposed Sales_Daily column layout** (new columns for payment methods)
2. **Affected code sections** with line references
3. **3 implementation approaches** (simple/minimal/full)
4. **Sheet migration plan** for existing data
5. **Estimate: files changed, lines added**

## Verification
- File exists at `/root/.coordination/TASK_payment_design.md`
- Contents cover all 5 deliverables
- Line references to main.py are accurate (file is 12,249 lines)

## IMPORTANT
- Use `path_mapping.json` keys, NOT raw paths
- Read COORDINATION.md first from `/root/.coordination/`
- Do NOT write code — this is a design/architecture task only
- Write completion to AGENT_STATUS.md when done
