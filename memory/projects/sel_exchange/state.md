# SEL Currency Exchange — Project State

## Status: Active ✅
**Last updated:** 2026-06-30 09:03 UTC

## Services
- `sel-exchange-api` — FastAPI on port 8001 ✅
- `sel-exchange-bot` — Telegram bot ✅

## DB State (clean for production)
- 4 accounts (Cash/Bank MMK, Cash/Bank THB)
- 5 contacts (2 suppliers, 3 customers)
- Sample transactions for testing

## Current Features
- [x] Buy/Sell transactions with multi-line payment breakdown
- [x] FIFO inventory tracking
- [x] FIFO PNL with daily/monthly/custom period
- [x] Receivable & Payable per-contact
- [x] 4-tab web dashboard
- [x] HMAC-SHA256 auth
- [x] Payment line charges (buy/payable only)
- [x] Charges excluded from paid_amount
- [x] Hourly auto-backup
- [x] Telegram bot

## Recent Changes (2026-06-30)
- [x] Contact edit (PATCH /api/counterparties/{cid}) with edit modal in dashboard
- [x] Duplicate name check on contact create & update (case-insensitive)
- [x] `esc()` JS helper for safe HTML attribute escaping
- `db.py`: Added `counterparty_update()`, `counterparty_get_by_name()`
- `app.py`: Added `CounterpartyUpdate` model, PATCH endpoint, duplicate checks
- `dashboard/index.html`: Edit button column, `editContact()` modal, save handler

## Known Issues
- Inventory tab not yet implemented in dashboard
- Bot may need updates for new payment line format

## Next Steps
- Boss to enter real transaction data
- Domain migration when new domain ready

## 2026-06-30 — OPEX Tab Added
- **New database table:** `opex` (id, category, description, amount, currency, payment_date, from_account_id, notes, created_at)
- **DB functions:** `opex_list()`, `opex_create()`, `opex_update()`, `opex_delete()`, `opex_summary()` — all with automatic account balance adjustments
- **API endpoints:** `GET/POST /api/opex`, `PATCH/DELETE /api/opex/{id}` — all auth-protected
- **Dashboard:** New "OPEX" tab in sidebar with summary cards, expense table, add/edit/delete modal forms, account dropdown integration
- **Dashboard summary:** `/api/dashboard` now includes `opex` field
- Account balances auto-adjust when OPEX is created (deduct), edited (reverse + re-apply), or deleted (reverse)
