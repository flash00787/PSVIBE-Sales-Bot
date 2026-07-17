# SEL Currency Exchange — Project State

## Status: Active ✅
**Last updated:** 2026-07-17 08:50 UTC

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

## Major Update: 2026-07-17 — Equity/Shareholder System Added

### New Database Tables
- **`shareholders`** — id, name, phone, notes, is_active, created_at, updated_at
- **`equity_transactions`** — id, shareholder_id, tx_type (inject/eject/dividend), amount, currency (THB/MMK), thb_account_id, mmk_account_id, notes, tx_date, period, created_at

### New API Endpoints (8 total)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/equity/shareholders` | List shareholders with computed net capital & dynamic share % |
| POST | `/api/equity/shareholders` | Create new shareholder |
| PATCH | `/api/equity/shareholders/{sid}` | Edit shareholder |
| GET | `/api/equity/transactions` | List equity transactions (filterable) |
| POST | `/api/equity/inject` | Capital injection in THB + creates FIFO buy tx |
| POST | `/api/equity/eject` | Capital ejection in THB + creates FIFO sell tx |
| POST | `/api/equity/dividend` | Distribute profit as dividends (MMK) by share % |
| GET | `/api/equity/summary` | Overall equity summary (total capital, dividends, shareholders) |

### New Dashboard Tab
- **📋 Equity tab** with summary cards (Total Capital, Injected, Ejected, Dividends)
- Shareholder table with dynamic % (progress bar)
- Equity transactions history
- Modal forms: Inject Capital, Eject Capital, Distribute Profit, Add Shareholder

### Key Business Logic
- **Dynamic Share %** = (shareholder net capital / total net capital) × 100
- **Inject THB** → equity_tx + buy transaction → feeds into FIFO inventory
- **Eject THB** → equity_tx + sell transaction → FIFO consumption
- **Dividend MMK** → auto-deducts from MMK account, distributes by current share %
- **FIFO Integration** — injects/ejects are fully tracked in FIFO cost basis

### Files Modified
- `db.py`: Added 10 equity DB functions + 2 new table schemas in init_db()
- `app.py`: Added 8 equity API endpoints with Pydantic models
- `dashboard/index.html`: Added Equity tab (HTML + JS) with 4 modal dialogs

## 2026-06-30 — OPEX Tab Added
- **New database table:** `opex` (id, category, description, amount, currency, payment_date, from_account_id, notes, created_at)
- **DB functions:** `opex_list()`, `opex_create()`, `opex_update()`, `opex_delete()`, `opex_summary()` — all with automatic account balance adjustments
- **API endpoints:** `GET/POST /api/opex`, `PATCH/DELETE /api/opex/{id}` — all auth-protected
- **Dashboard:** New "OPEX" tab in sidebar with summary cards, expense table, add/edit/delete modal forms, account dropdown integration
- **Dashboard summary:** `/api/dashboard` now includes `opex` field
- Account balances auto-adjust when OPEX is created (deduct), edited (reverse + re-apply), or deleted (reverse)

## Known Issues
- Bot token is invalid (BOT_TOKEN has literal `***` prefix)
- No real transaction data entered yet (accounts have opening balances only)
