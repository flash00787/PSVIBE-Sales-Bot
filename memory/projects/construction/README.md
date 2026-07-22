# Three Brothers Construction Bot — Comprehensive README

> **Version:** 1.0.0 | **Owner:** Ko Aung Chan Myint | **GitHub:** flash00787/construction-bot  
> **Framework:** Telegraf.js v4.16.3 | **Database:** Google Sheets (Google Spreadsheet API v4)  
> **Deployment:** Docker (construction_bot container) | **Language:** Node.js (v22 Alpine)

---

## 1. Project Overview & Purpose

The **Three Brothers Construction Bot** is a Telegram-based enterprise accounting and management system built for a Myanmar construction company. It replaces manual bookkeeping by providing:

- **Transaction Entry** — Double-entry style income/expense recording by project
- **Asset Management** — Machinery/vehicle/equipment register with straight-line depreciation
- **Procurement** — Materials purchasing with FIFO inventory tracking
- **Payables/Receivables** — Credit tracking with pending/settled statuses
- **Subcontract Management** — Subcontract creation with payment tracking
- **Equipment & Driver Management** — Equipment rental income, maintenance logs, driver advances/pay
- **OPEX Tracking** — Company overhead (rent, salaries, utilities, etc.)
- **Equity Module** — 7 shareholders + Operation Manager (OM) bonus at 30% of gross profit
- **Financial Reports** — Dashboard, Summary, Monthly/Annual P&L, Balance Sheet, Cash Flow, Project P&L
- **Inventory Management** — FIFO-based purchase/transfer/sell with cost auto-computation

### Initial Capital: 360,000,000 MMK (7 shareholders, fixed ratios)

---

## 2. Architecture Diagram

```
┌────────────────────────────────────────────────────┐
│                  Telegram User                      │
│            (Bot commands / inline buttons)           │
└──────────────────────┬─────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────┐
│                 Telegraf.js (bot.js)                 │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐ │
│  │ Scenes   │  │ Reports  │  │  Navigation       │ │
│  │ (Wizards)│  │ (Async)  │  │  (Keyboards/Menus)│ │
│  └────┬─────┘  └────┬─────┘  └────────┬──────────┘ │
│       │              │                 │            │
│  ┌────┴──────────────┴─────────────────┴──────────┐ │
│  │            Google Sheets Interface              │ │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────┐ │ │
│  │  │ getDoc()   │  │ Tab CRUD   │  │ 30s Cache │ │ │
│  │  │ (JWT Auth) │  │ (Add/Read) │  │ (in-mem)  │ │ │
│  │  └────────────┘  └────────────┘  └───────────┘ │ │
│  └──────────────────────┬──────────────────────────┘ │
└──────────────────────────┼───────────────────────────┘
                           │ Google Sheets API v4
                           ▼
┌────────────────────────────────────────────────────┐
│             Google Spreadsheet                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐│
│  │ Data Tabs│ │ Report   │ │ Config/Reference     ││
│  │ 20+ tabs │ │ Tabs     │ │ Tabs                 ││
│  └──────────┘ └──────────┘ └──────────────────────┘│
└────────────────────────────────────────────────────┘
```

---

## 3. Complete Bot Command List

| Command | Description |
|---------|-------------|
| `/start` | Main menu with active project list |
| `/menu` | Go to main menu |
| `/add_entry` | Start transaction entry wizard |
| `/project` | Create new project wizard |
| `/asset` | Register new asset wizard |
| `/payable` | Add payable wizard |
| `/receivable` | Add receivable wizard |
| `/advance` | Advance payment wizard |
| `/summary` | Financial summary/dashboard |
| `/recent` | Latest 5 transactions+OPEX |
| `/cancel` | Cancel current wizard operation |
| `/help` | Bot command reference |

### Keyboard Shortcuts (Main Menu)
- `📝 စာရင်းသွင်း` — Transaction Entry
- `📊 Summary` — Financial Overview
- `📋 Recent` — Recent Transactions
- `📂 View Lists` — List Payables/Receivables/Advances/Assets/Projects
- `⚙️ Admin` — Admin Panel (6 categories)

---

## 4. Admin Panel Structure

### Category: 🏗️ Projects
- New Project, Rename Project, Close Project, Project P&L
- Asset Register, Delete Asset

### Category: 💰 Finance & Equity
- Add Payable, Receivable, Advance Payment, OPEX Entry
- Equity/Dividend Info, Account Transfer

### Category: 🔩 Procurement
- Materials Purchase (FIFO inventory), New Subcontract, Subcontract Payment

### Category: 🚛 Equipment & Drivers
- Equipment Rental, Maintenance Log, Equipment P&L
- Driver Register, Driver Pay, Driver Advance

### Category: 📊 Reports & Data
- Monthly P&L, Annual P&L, Cash Flow, Balance Sheet
- View Lists, Inventory, Account Balances, Manage Transactions

### Category: ⚙️ System
- Reload Config, Setup Tabs, Help, Reset All Data

---

## 5. All Scene Wizards with Step-by-Step Flow

### WIZARD 1: Transaction Entry (`entryWizard`, scene "ENTRY")
7-step wizard for recording project income/expense:
1. **Project Select** — Active projects from Projects_Master
2. **Type** — Income (ဝင်ငွေ) or Expense (အသုံးစရိတ်)
3. **Account** — From COA (Accounts filtered by type; Material→sub-type picker)
4. **Amount** — Float input (MMK)
5. **Description** — Free text (optional, skip via button)
6. **Payment Method** — Cash / Bank Transfer / YOMA Bank / Cheque / On Credit
7. **Confirm & Save** → Appended to `Transactions` tab

### WIZARD 2: Project Create (`projectWizard`, scene "PROJECT")
6-step wizard:
1. Project Name, 2. Project Type, 3. Client/Employer, 4. Contract Value, 5. Start Date, 6. Notes → Confirm & Save to `Projects_Master`

### WIZARD: Rename Project (`renameProjectWizard`, scene "RENAME_PROJECT")
3-step wizard: pick project → type new name → confirm (updates both Projects_Master + all Transactions rows)

### WIZARD 3: Asset Register (`assetWizard`, scene "ASSET")
9-step wizard:
1. Asset Name, 2. Asset Type, 3. Purchase Date, 4. Purchase Cost, 5. Salvage Value, 6. Useful Life (years), 7. Assigned Project, 8. Notes, 9. Payment Method → Saves to `Assets_Master` with auto-calculated Monthly_Depreciation

### WIZARD 4: Payable (`payableWizard`, scene "PAYABLE")
6-step wizard:
1. Supplier Name, 2. Project, 3. Category, 4. Amount, 5. Due Date, 6. Description → Confirm & Save to `Payables`

### WIZARD 5: Receivable (`receivableWizard`, scene "RECEIVABLE")
6-step wizard:
1. Client Name, 2. Project, 3. Invoice No., 4. Amount, 5. Due Date, 6. Description → Confirm & Save to `Receivables`

### WIZARD 6: Advance Payment (`advanceWizard`, scene "ADVANCE")
7-step wizard:
1. Type (ပေးသည်/ရသည်), 2. To/From, 3. Project, 4. Amount, 5. Purpose, 6. Expected Return Date, 7. Payment Method → Saves to `Advance_Payments`

### WIZARD 7: OPEX Entry (`opexWizard`, scene "OPEX")
6-step wizard:
1. OPEX Category, 2. Amount, 3. Date (with normalization), 4. Description, 5. Payment Method → Saves to `OPEX`

### WIZARD: Dividend (`dividendWizard`, scene "DIVIDEND")
5-step wizard:
1. Show shareholder list with available amounts, 2. Select shareholder, 3. Amount, 4. Payment method, 5. Note → Saves to `Dividends`

### WIZARD: OM Bonus (`omBonusWizard`, scene "OM_BONUS")
4-step wizard:
1. Show auto-calculated 30% of gross profit, 2. Amount, 3. Payment method, 4. Confirm → Saves to `OM_Bonus`

### WIZARD: Inventory Add Material (`addMatWizard`, scene "INV_ADDMAT")
3-step wizard:
1. Material Name, 2. Unit (from list), 3. Category → Saves to `Materials_Master` with auto-generated MAT-XXX code

### WIZARD: Material Edit (`matEditWizard`, scene "MAT_EDIT")
3-step wizard:
1. Show current info + choose field to edit, 2. Enter new value, 3. Confirm → Updates `Materials_Master`

### WIZARD: Inventory Purchase (`invBuyWizard`, scene "INV_BUY")
6-step wizard:
1. Select Material from catalog, 2. Qty, 3. Unit Price, 4. Payment Method, 5. Notes, 6. Confirm → Creates `Inventory_Lots` lot + `Inventory_Movements` record + Transaction/Payable

### WIZARD: Inventory Transfer (`invTransferWizard`, scene "INV_TRANSFER")
6-step wizard:
1. Select Material (with stock levels), 2. Qty (validated against stock), 3. Project, 4. Notes, 5. FIFO cost preview + confirm, 6. FIFO consume → Creates Movement + Materials_Purchases entry

### WIZARD: Inventory Sell (`invSellWizard`, scene "INV_SELL")
Similar to Transfer but records as Income (Sale) instead of direct materials cost

### WIZARD: Edit Transaction (`editTxWizard`, scene "EDIT_TX")
3-step wizard:
1. Select field to edit (from TX_COLS), 2. Enter new value (project/account/type/payment via picker, text via keyboard), 3. Save directly to sheet row

### WIZARD: Insert Transaction (`insertWizard`, scene "INSERT_TX")
8-step wizard: Same flow as Transaction Entry but starts with custom date selection

### WIZARD: Account Transfer (`accTransferWizard`, scene "ACC_TRANSFER")
4-step wizard:
1. From Account (with balance), 2. To Account, 3. Amount, 4. Notes → Saves to `Account_Transfers`

### WIZARD: Equipment Rental (`equipRentWizard`, scene "EQUIP_RENT")
Records equipment rental income to `Equipment_Rentals` tab

### WIZARD: Maintenance Log (`maintWizard`, scene "NEW_MAINT")
Records maintenance events to `Maintenance_Log` tab

### WIZARD: Subcontract (`subcontractWizard`, scene "NEW_SUBCONTRACT")
Creates subcontract entries with Contract_Amount to `Subcontracts` tab

### WIZARD: Subcontract Payment (`subPayWizard`, scene "NEW_SUBPAY")
Records payment against existing subcontract to `Subcontract_Payments` + updates Remaining

### WIZARD: Driver Payment (`driverPayWizard`, scene "DRIVER_PAY")
Records driver salary/Labor payments to `Driver_Payments` tab

### WIZARD: Driver Advance (`driverAdvWizard`, scene "DRIVER_ADV")
Records advance given to drivers with Receivable/Deductible tracking to `Driver_Advances`

### WIZARD: Driver Master (`driverMasterWizard`, scene "DRIVER_MASTER")
Registers new driver in `Drivers_Master` with assigned equipment

### WIZARD: Materials Purchase (`matPurchaseWizard`, scene "MAT_PURCHASE")
Records direct materials purchases to `Materials_Purchases` tab

---

## 6. Google Sheets Tab Structure (22 tabs)

### Data Entry Tabs
| Tab Name | Headers | Purpose |
|----------|---------|---------|
| **Transactions** | Date, Project_Name, Account_Type, Account_Name, Amount, Description, Payment_Method | Core journal entries |
| **OPEX** | Date, OPEX_Category, Amount, Description, Payment_Method | Operating expenses (no project) |
| **Account_Transfers** | Transfer_ID, Date, From_Account, To_Account, Amount, Notes | Cash/Bank transfers |
| **Advance_Payments** | Date, Type, To_From, Project, Amount, Purpose, Expected_Return, Payment_Method, Status | Advances (ကြိုးငွေ) |
| **Assets_Master** | Asset_ID, Asset_Name, Asset_Type, Purchase_Date, Purchase_Cost, Assigned_Project, Useful_Life_Years, Salvage_Value, Monthly_Depreciation, Payment_Method, Status, Notes | Fixed asset register |
| **Projects_Master** | Project_ID, Project_Name, Project_Type, Client, Contract_Value, Start_Date, Status, Notes | Construction projects |
| **Payables** | Date, Supplier, Project, Category, Amount, Due_Date, Status, Notes | Accounts payable |
| **Receivables** | Date, Client, Project, Invoice_No, Amount, Due_Date, Status, Notes | Accounts receivable |
| **Dividends** | Date, Member, Amount, Payment_Method, Notes | Shareholder dividends |
| **OM_Bonus** | Date, Amount, Payment_Method, Notes | Operation Manager bonus |
| **Materials_Master** | Material_Code, Material_Name, Unit, Category, Active | Material catalog |
| **Inventory_Lots** | Lot_ID, Date, Material_Code, Material_Name, Unit, Original_Qty, Remaining_Qty, Unit_Price, Total_Cost, Status, Notes | FIFO inventory lots |
| **Inventory_Movements** | Mov_ID, Date, Type, Material_Code, Material_Name, Unit, Qty, Unit_Price, Total_Amount, Project, Notes | Inventory movement log |
| **Materials_Purchases** | Date, Project_Name, Material_Name, Unit, Qty, Unit_Price, Total_Cost, Payment_Method, Notes | Direct/transfer materials cost |
| **Subcontracts** | Subcontract_ID, Date, Project_Name, Contractor_Name, Scope, Contract_Amount, Amount_Paid, Remaining, Status, Notes | Subcontract tracking |
| **Subcontract_Payments** | Payment_ID, Date, Subcontract_ID, Project_Name, Contractor_Name, Amount, Payment_Method, Notes | Subcontract payment log |
| **Equipment_Rentals** | Rental_ID, Date, Equipment_Name, Renter_Name, Rental_Period, Amount, Payment_Method, Status, Notes | Equipment rental income |
| **Maintenance_Log** | Maint_ID, Date, Equipment_Name, Maint_Type, Description, Amount, Payment_Method, Notes | Maintenance records |
| **Driver_Payments** | Date, Driver_Name, Payment_Type, Equipment_Name, Amount, Payment_Method, Notes | Driver salary payments |
| **Driver_Advances** | Advance_ID, Date, Driver_Name, Amount_Given, Amount_Deducted, Remaining, Payment_Method, Advance_Type, Status, Notes | Driver advances |
| **Drivers_Master** | Driver_ID, Driver_Name, Phone, Assigned_Equipment, License_No, Join_Date, Status, Notes | Driver registry |

### Reference & Config Tabs
| Tab Name | Purpose |
|----------|---------|
| **Chart_of_Accounts** | 23+ accounts across 5 types (Income, Expense, Asset, Liability, Equity) |
| **Config** | Dynamic configuration: OPEX_Category, Project_Type, Asset_Type, Payable_Category |

### Report Tabs (Auto-formula)
| Tab Name | Content |
|----------|---------|
| **Dashboard_Data** | 12 metrics (Revenue, Expense, Profit, Assets, Liabilities, etc.) with Current_Month + All_Time |
| **Project_PnL** | QUERY-based Revenue/Expense by Project |
| **Balance_Sheet** | Assets = Liabilities + Equity with SUMIF formulas |
| **Cash_Flow** | Operating/Investing/Financing cash flow |
| **Machinery_Report** | Machinery profitability with monthly depreciation |
| **Monthly_Summary** | Last 12 months Income/Expense/Net with Payables/Receivables settled |
| **Project_Ledger** | Per-project contract value, income, expense, net profit |

---

## 7. Account/COA Structure

### Account Types & Accounts (live-loaded from Chart_of_Accounts sheet)

| Type | Accounts | Normal Balance |
|------|----------|----------------|
| **Income** | Contract Revenue, Machinery Rental Income, Consultation Fees, Other Income | Credit |
| **Expense** | Direct Materials, Direct Labor, Subcontractor Costs, Equipment Rental, Fuel & Lubricants, Maintenance & Repairs, Office Salaries, Transportation, Utilities, Material, Other Expense | Debit |
| **Asset** | Project Premium Receivable (5%), Project Insurance Receivable (2%), Other Receivable, Prepaid Expense | Debit |
| **Liability** | Accounts Payable, Accrued Expenses, Tax Payable, Loans Payable | Credit |
| **Equity** | Dividends Distributed | Debit |

### Shareholder Structure
| Shareholder | Capital (MMK) | Ratio |
|-------------|--------------|-------|
| Ye Myat | 60,000,000 | 16.67% |
| Aung Chan Myint | 60,000,000 | 16.67% |
| Min Hset Paing | 60,000,000 | 16.67% |
| Wai Yan Aung | 60,000,000 | 16.67% |
| Zin Min Khant | 60,000,000 | 16.67% |
| Zaw Myo Htwe | 30,000,000 | 8.33% |
| Htain Lin | 30,000,000 | 8.33% |
| **TOTAL** | **360,000,000** | **100%** |

### Operation Manager: U Than Tun Aung — 30% of Gross Profit

---

## 8. Key Code Patterns & Conventions

### Wizard Pattern
Every wizard follows the same structure:
```javascript
const myWizard = new Scenes.WizardScene("SCENE_ID",
  async ctx => { /* step 0 — init & first message */ return ctx.wizard.next(); },
  async ctx => { /* step 1 */ },
  // ...more steps...
  async ctx => { /* final step — save & leave */ return ctx.scene.leave(); }
);
myWizard.command("cancel", ctx => endScene(ctx, "❌ Cancelled."));
```

### Form Builder Pattern
`buildForm(title, fields, activeStep)` renders a progress bar + field list. Fields with values show "✅ value", active step shows "⬇️", future steps show the label only. Progress bar uses ▓/░ chars scaled to 8 blocks.

### Message Editing Pattern
All wizard UIs edit a single message (prevents chat spam):
- `initScene()` — sends first message, stores msgId/chatId
- `editForm()` — edits stored message or falls back to new reply
- `endScene()` — edits to final message with "🏠 Menu" button

### Handler Pattern
```
handleCbText(ctx, allowed, onMatch) — callback query handler with Cancel support
handleTextInput(ctx, onValid, validate) — text input with auto-delete, cancel, validation
renderXxxStep(ctx, step) — re-renders form at specific step
```

### Google Sheets CRUD Pattern
```javascript
getOrCreateTab(tabName, headers) — ensures tab exists with correct headers
appendToTab(tabName, headers, row) — adds row, invalidates cache
getTabRows(tabName, limit) — reads with 30s TTL cache
clearTabData(tabName) — clears sheet, preserves canonical headers
markRowStatus(tabName, rowNumber, newStatus) — updates status cell
getNextId(prefix, tabName) — auto-incremented ID generation
```

### Cache Strategy
- 30-second TTL in-memory Map cache
- `_cacheKey(tabName)` → `tab:<tabName>` keys
- Invalidated on write (`_cacheInvalidate(tabName)`)
- Cache hit/miss logged to console

### Config/COA Refresh
- `refreshAccounts()` — Loads COA from Chart_of_Accounts tab at startup
- `refreshConfig()` — Loads OPEX_Category, Project_Type, Asset_Type, Payable_Category from Config tab
- `refreshProjects()` — Loads Active projects from Projects_Master
- All called in sequence at bot startup: `await Promise.all([refreshAccounts(), refreshConfig(), refreshProjects()])`

### Date Normalization
`normalizeDate()` handles multiple formats: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY

### Payment Methods
Cash, Bank Transfer, YOMA Bank, Cheque, On Credit

### Account Balances
`getAccountBalances()` computes running balance across ALL tabs: Transactions, OPEX, Account_Transfers, Advance_Payments, Assets_Master, OM_Bonus, Dividends. Starts with 360M in Bank Transfer.

### Project P&L Computation
`getProjectDetailedPnL()` reads three tabs:
- **Transactions** → income + other expenses (excluding Direct Materials, Subcontractor Costs)
- **Materials_Purchases** → total materials cost per project
- **Subcontracts** → contract amount + paid per project

### FIFO Inventory System
- `fifoConsume()` — Consumes lot rows oldest-first, updates Remaining_Qty, sets Status to Partial/Closed
- `fifoPreview()` — Read-only FIFO cost preview with breakdown per lot
- Purchase → creates Lot (Open) + Inventory Movement + optionally Transaction or Payable
- Transfer → FIFO consume + Inventory Movement + Materials_Purchases entry
- Sell → FIFO consume + records as equipment/project Income

---

## 9. Data Flow Diagrams

### Transaction Entry Flow
```
User → /add_entry → Load Projects from Cache/Sheet
  → Select Project → Select Income/Expense → Select Account (filtered)
  → Enter Amount → Enter Description → Select Payment Method
  → Confirm → appendToTab("Transactions", ...) → Invalidate Cache → Done
```

### Financial Report Flow
```
User → /summary → Load all tabs (Transactions + OPEX + Materials + Subcontracts + etc.)
  → calcYearProfit() — compute income/expense/opex/materials/subcontracts
  → getAccountBalances() — compute cash balance across all tabs
  → Format & Display with inline keyboard to other reports
```

### Config/COA Refresh Flow
```
Bot Start → refreshAccounts() → Read Chart_of_Accounts tab → Populate accountsCache
          → refreshConfig() → Read Config tab → Populate ASSET_TYPES/PROJECT_TYPES/PAY_CATEGORIES/OPEX_CATS
          → refreshProjects() → Read Projects_Master → Populate projectCache (Active only)
          → Bot ready for requests
```

---

## 10. Deployment & Configuration

### Environment Variables (.env)
```
BOT_TOKEN=telegram_bot_token
GOOGLE_SERVICE_ACCOUNT_EMAIL=service-account@project.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
SPREADSHEET_ID=google_sheets_document_id
ALLOWED_USER_IDS=comma_separated_telegram_user_ids
```

### Docker Deployment
```bash
cd /opt/construction-bot
docker compose up -d --build
```

### Container Specs
- **Image:** node:22-alpine
- **Container:** construction_bot
- **Restart:** unless-stopped
- **Volume:** bot.js mounted as :ro (read-only)
- **Logging:** json-file, 10MB max, 3 files rotation

### Setup Scripts
- `setup-sheets.js` — Creates all 6 data tabs + Dashboard + Monthly Summary + Project Ledger + COA
- `full-setup-sheet.js` — Creates ALL tabs with formulas (Balance Sheet, Cash Flow, P&L, Dashboard, Machinery)
- `add-material-sheet.js` — Adds "Material" to Chart_of_Accounts
- `cash_calc.js` — Standalone cash balance computation across all tabs

### Build-Time Patches
- `patches/patch-polling.js` — Applied during Docker build (modifies telegraf to use long-polling)

---

## 11. Utility Functions Reference

| Function | Purpose |
|----------|---------|
| `chunk(arr, n)` | Split array into groups of n |
| `kb(labels, cols, extra)` | Build inline keyboard from labels |
| `now()` | Current timestamp YYYY-MM-DD HH:MM:SS |
| `today()` | Current date YYYY-MM-DD |
| `parseAmt(v)` | Parse amount string (removes commas/spaces) |
| `fmtNum(n)` | Format number with MMK locale (or "—" for empty) |
| `normalizeDate(dt)` | Convert DD/MM/YYYY to YYYY-MM-DD |
| `getPrivateKey()` | Decode ENV private key |
| `getDoc()` | Singleton Google Sheets connection (lazy) |
| `getOrCreateTab()` | Ensure tab exists with headers |
| `appendToTab()` | Add row + invalidate cache |
| `getTabRows()` | Read rows with 30s cache |
| `clearTabData()` | Clear tab, keep canonical headers |
| `getDashboardMetrics()` | Read Dashboard_Data tab |
| `getNextId()` | Auto-increment ID (PRJ-001, AM-001, etc.) |
| `markRowStatus()` | Update Status cell on a row |
| `buildForm()` | Render form progress UI |
| `editForm()` | Edit or resend telegram message |
| `initScene()` | Send first scene message, store msgId |
| `endScene()` | Edit final message, leave scene |
| `handleCbText()` | Handle callback with Cancel support |
| `handleTextInput()` | Handle text input with auto-delete |
| `calcYearProfit()` | Compute full P&L from all tabs |
| `calcAccumDep()` | Compute accumulated depreciation since May 2026 |
| `getAccountBalances()` | Compute running balance across all tabs |
| `getProjectPnL()` | Simple project P&L from Transactions |
| `getProjectDetailedPnL()` | Enhanced P&L from 3 tabs |
| `fifoConsume()` | FIFO stock consumption |
| `fifoPreview()` | Read-only FIFO cost estimate |
| `getInventoryStatus()` | Current stock levels |
| `sendMainMenu()` | Main keyboard menu |
| `sendSummary()` | Financial overview |
| `sendMonthlyReport()` | Last 6 months P&L |
| `sendAnnualReport()` | Year picker → full annual P&L |
| `sendBalanceSheetReport()` | Assets = Liabilities + Equity |
| `sendCashFlowReport()` | Operating/Investing/Financing |
| `sendEquityInfo()` | Equity/dividend distribution |
| `sendDepreciationDetail()` | Asset depreciation schedule |

---

## 12. Known Constraints & Design Decisions

- **Single-file architecture** — 6837 lines in bot.js, no modular splitting
- **Google Sheets as DB** — No SQL/NoSQL. Pros: human-readable, no extra infrastructure. Cons: API latency, rate limits, cell-based updates slow for bulk
- **30-second cache** — Balances stale reads with freshness. Write operations invalidate cache. Cache keys use tab names.
- **Ephemeral user messages** — User input messages are auto-deleted to keep chat clean
- **Single message editing** — All wizard steps edit one message to avoid spam
- **Material sub-types** — "Material" account triggers a Steel/Cement/Sand/Aggregate/Brick sub-picker
- **Equipment project** — Project "Equipment" used as sentinel for equipment/driver-related transactions, filtered out from construction P&L
- **Dedicated tabs prevent double-entry** — Direct Materials and Subcontractor Costs excluded from Transaction entry (must use Materials Purchase and Subcontract Payment wizards)
- **OM Bonus** — Auto-calculation at 30% of gross profit, but manual recording wizard
- **Initial capital** — 360M treated as already in Bank Transfer, not tracked as transaction
- **Depreciation Start** — Hardcoded to May 1, 2026. Months are computed from that date.
- **ALLOWED_USER_IDS** — Optional access control (bot works for all if not set)
