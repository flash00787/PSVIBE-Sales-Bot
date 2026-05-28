# V2 Fix Coordination — 2026-05-27

## Shared Context

### V2 Code Location (VPS)
- **Sales Bot V2 Root:** `/root/Aung Chan Myint/Sales-Tele-Bot/`
  - `bot/__init__.py` (1,739 lines) — Shared utilities, sheets, globals
  - `bot/app.py` (455 lines) — App setup, main(), auth middleware, ConversationHandler
  - `bot/handlers.py` (12,134 lines) — All handler functions
  - `api_server/api_server.js` — Node.js API server (receipts, bookings, analytics)
  - `main.py` (12,266 lines) — Monolithic V1 (still running)

### V2 Known Issues (from prior work)
- Import bugs between modules (shared state across bot/__init__.py, bot/app.py, bot/handlers.py)
- now_mmt() function needed
- _ALLOWED_USER_IDS must be consistent
- Monolithic code + modular code exist as parallel copies

### Google Sheets
- **SHEET_ID:** `1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA`
- **Tabs:** Card_wallet, Sales_Daily, TopUp_Log, Stock_In, Salary_Advance, Analytics (see .env)
- **Service account:** `/root/Aung Chan Myint/Sales-Tele-Bot/service_account.json`

### Available scripts
- **start.sh:** Starts V1 main.py
- **Deploy:** `/root/Aung Chan Myint/.coordination/` has deploy/rollback scripts (if present)

## Agents Assigned

### Agent 1: API Fix
**Model:** deepseek/deepseek-v4-pro
**Task:** Fix api_server.js issues
- Fix port binding / EADDRINUSE issue
- Fix service file path to match actual directory
- Ensure all endpoints work (bookings, consolestatus, analytics)
- Verify env vars are properly loaded
- Add systemd service file fix (psvibe-api.service)

### Agent 2: Database Fix
**Model:** deepseek/deepseek-v4-pro
**Task:** Fix database / Google Sheets layer issues
- Verify all Sheets tabs are accessible
- Fix any gspread/oauth2 issues in bot/__init__.py
- Ensure Card_wallet Column H (Balance Mins) reads correctly
- Fix sheet write/update logic
- Check retry wrapper works

### Agent 3: Receipt URLs Fix
**Model:** deepseek/deepseek-v4-pro
**Task:** Fix receipt URL generation and templates
- Fix receipt HTML templates in api_server.js
- Fix receipt URL paths (API_BASE_URL + /api/receipt/:id)
- Verify receipt CSS/print styles
- Remove Burmese footer text from receipts
- Test receipt generation flow

### Agent 4: Home Button Fix
**Model:** deepseek/deepseek-v4-pro
**Task:** Fix home/back button navigation
- Fix Home button in handlers.py (show_main_menu, back handlers)
- Fix ConversationHandler states to allow return to main menu
- Verify all callback query handlers have proper navigation
- Ensure consistent back/home behavior across all flows

### Agent 5: Full Audit
**Model:** anthropic/claude-sonnet-4-20250514
**Task:** Cross-check ALL logic between Google Sheets and Sales Bot code
- Read all sheet column mappings from code vs actual Sheets
- Verify: Sales_Daily, TopUp_Log, Stock_In, Salary_Advance column positions
- Check Card_wallet Column H (Balance Mins) usage is correct
- Verify analytics calculations
- Check V1 main.py vs V2 modular code for logic parity
- Produce audit report

## Completion
Each agent writes completion status to `/root/Aung Chan Myint/.coordination/AGENT_STATUS.md`
Format:
```
## Agent: [Name] — YYYY-MM-DD HH:MM UTC
**Task:** [task]
**Status:** PASS/FAIL
**Notes:** [summary]
**Files changed:** [file list]
```
