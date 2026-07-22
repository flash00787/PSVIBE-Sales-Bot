# Three Brothers Construction Bot — Project State

> **Last Updated:** 2026-07-22  
> **Status:** Active / Production  
> **Container:** construction_bot (Docker)  
> **Code Version:** v1.0.0

---

## Architecture Overview

Single-file Telegram bot (`bot.js`, 6837 lines) using Telegraf.js Scene-based Wizard system with Google Sheets as the sole backend database. All data stored in a single Google Spreadsheet with 22+ tabs. In-memory 30-second TTL cache for reads. JWT authentication for Google Sheets API.

### Core Components

1. **Wizard Engine** — 20+ Scene Wizards for structured data entry
2. **Google Sheets Interface** — Singleton connection, tab CRUD, cache layer
3. **Report Generators** — Financial statements computed from raw data
4. **Navigation System** — Inline keyboard menus (6 admin categories, view lists, settle menus)
5. **Equity Module** — 7 shareholders + OM bonus (30%) computation
6. **FIFO Inventory** — Materials catalog, lot tracking, consumption, cost preview
7. **Config System** — Live-loaded COA, project types, OPEX categories from sheets

### Wizard Scenes (20+)
entryWizard, projectWizard, renameProjectWizard, assetWizard, payableWizard, receivableWizard advanceWizard, opexWizard, dividendWizard, omBonusWizard, addMatWizard, matEditWizard invBuyWizard, invTransferWizard, invSellWizard, editTxWizard, insertWizard accTransferWizard, equipRentWizard, maintWizard, subcontractWizard, subPayWizard driverPayWizard, driverAdvWizard, driverMasterWizard, matPurchaseWizard

### Report Functions
sendSummary, sendMonthlyReport, sendAnnualReport, sendBalanceSheetReport sendCashFlowReport, sendEquityInfo, sendDepreciationDetail, sendAccountBalances sendRecent, sendViewLists, sendManageTx, sendInventoryView, sendInvMovements

---

## Data Flow

```
Telegram User → bot.js → Google Sheets
                           ├── Transactions (journal entries)
                           ├── OPEX (overhead)
                           ├── Payables/Receivables (credit tracking)
                           ├── Assets_Master (depreciation)
                           ├── Projects_Master (active projects)
                           ├── Materials_Master + Inventory_Lots + Inventory_Movements (FIFO)
                           ├── Materials_Purchases + Subcontracts (dedicated procurement)
                           ├── Equipment_Rentals + Maintenance_Log (equipment)
                           ├── Driver_Payments + Driver_Advances + Drivers_Master
                           ├── Dividends + OM_Bonus (equity module)
                           ├── Chart_of_Accounts + Config (reference)
                           └── Report tabs (auto-formulas for Dashboard, P&L, Balance Sheet, Cash Flow)
```

---

## Component Mapping

| Component | Location | Lines |
|-----------|----------|-------|
| Config/COA cache | bot.js ~L10-140 | 130 |
| Utilities | bot.js ~L140-230 | 90 |
| Google Sheets CRUD | bot.js ~L230-400 | 170 |
| Form Builder | bot.js ~L400-460 | 60 |
| Wizard Helpers | bot.js ~L460-510 | 50 |
| Transaction Entry | bot.js ~L510-700 | 190 |
| Project Create | bot.js ~L700-870 | 170 |
| Rename Project | bot.js ~L870-1020 | 150 |
| Asset Register | bot.js ~L1020-1210 | 190 |
| Payable | bot.js ~L1210-1370 | 160 |
| Receivable | bot.js ~L1370-1530 | 160 |
| Advance Payment | bot.js ~L1530-1710 | 180 |
| Equity/Dividend Module | bot.js ~L1710-2000 | 290 |
| OPEX Entry | bot.js ~L2000-2180 | 180 |
| Reports (Summary, Recent, Help, Lists, Settle) | bot.js ~L2180-2600 | 420 |
| Financial Statements (Monthly, Annual, Dep, Balances, BS, CF) | bot.js ~L2600-3300 | 700 |
| Inventory System (Catalog, Purchase, Transfer, Sell) | bot.js ~L3300-4300 | 1000 |
| Transaction Management (Edit, Insert, List, Delete) | bot.js ~L4300-5000 | 700 |
| Account Transfer | bot.js ~L5000-5150 | 150 |
| Equipment/Driver Wizards | bot.js ~L5150-6000 | 850 |
| Subcontract Wizards | bot.js ~L6000-6400 | 400 |
| Materials Purchase + System | bot.js ~L6400-6837 | 437 |

---

## Known Patterns & Design Decisions

### Scene Wizard Convention
- Every wizard uses `Scenes.WizardScene` with step-by-step async handlers
- `initScene()` on step 0 to set msgId/chatId
- `editForm()` for all subsequent UI updates (edits message, falls back to new message)
- `endScene()` on completion to show final confirmation
- `.command("cancel", ...)` on every wizard for cancellation
- `renderXxxStep(ctx, step)` helper for re-rendering specific steps

### Payment Methods
Cash, Bank Transfer, YOMA Bank, Cheque, On Credit — used across all wizards

### Cache Design
- Map-based, 30 second TTL
- Cache keys: `tab:<tabName>`
- Invalidation on writes
- Console logging for cache hits/misses

### Google Sheets Auth
- JWT service account with google-spreadsheet library
- Private key from ENV with `\n` replacement
- Singleton `getDoc()` pattern (lazy init, persistent)

### Number/Date Handling
- `parseAmt()`: removes commas, parses float
- `fmtNum()`: "—" for empty, locale string for numbers
- `normalizeDate()`: multi-format date parser (MM/DD/YYYY → YYYY-MM-DD)

### Dedicated Tabs for Accrual Tracking
- Materials not tracked in Transactions (use Materials_Purchases tab)
- Subcontracts tracked in dedicated Subcontracts + Subcontract_Payments tabs
- Equipment/Driver costs filtered by Project="Equipment" sentinel

---

## Deployment Info

| Property | Value |
|----------|-------|
| Host | bot-server-01 (5.223.81.16) |
| Container | construction_bot |
| Image | node:22-alpine |
| Port | None (Telegram webhook/polling) |
| Restart | unless-stopped |
| ENV | /opt/construction-bot/.env |
| Volumes | bot.js:ro |
| Logging | json-file, max-size 10m, max-file 3 |
| Health Check | `docker ps --filter name=construction_bot` |
| Test Command | `node --check /opt/construction-bot/bot.js` |
| Backup | construction_*.tar.gz in /root/backups/ |

### Google Sheet
- Spreadsheet ID: `19zHR6Ci2jSTZv-svYxk7wvHhhdbJmt_-GJ-g-8ZhtMw`
- 22+ tabs across data entry, reference, and reports
- Auto-formulas for Dashboard, Balance Sheet, Cash Flow, P&L

### Setup Scripts
- `full-setup-sheet.js` — Complete tab creation with formulas
- `setup-sheets.js` — Core data tabs + Dashboard + Monthly Summary + Project Ledger + COA
- `add-material-sheet.js` — Adds Material to COA
- `clear-data.js` — Data clearing utility
- `cash_calc.js` — Standalone balance computation
- `patches/patch-polling.js` — Telegraf polling patch for Docker

### Dependencies
```json
{
  "telegraf": "^4.16.3",
  "google-spreadsheet": "^4.1.5",
  "google-auth-library": "^9.15.1",
  "dotenv": "^16.6.1"
}
```

---

## Verification Status
- ✅ README.md created with complete wizard list, tab structure, patterns
- ✅ state.md created with architecture, deployment info
- ⬜ MongoDB trace entries (pending)
- ⬜ auto_doc_updater.py run (after MongoDB)
