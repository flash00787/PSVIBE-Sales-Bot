# SEL Currency Exchange — Project State

## Status: Active ✅
**Last updated:** 2026-06-25 18:11 UTC

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

## Known Issues
- Inventory tab not yet implemented in dashboard
- Bot may need updates for new payment line format

## Next Steps
- Boss to enter real transaction data
- Domain migration when new domain ready
