# PS VIBE Bot System — Technical Explanation
> Version: pre-Phase4 monolithic (main.py 12,249 lines)
> Source: Provided by Boss (Aung Chan Myint) on 2026-05-27
> Saved by: Kora

---

## 1. System Overview (Big Picture)

```
[Staff Telegram] [Customer Telegram]
 │ │
 ▼ ▼
 main.py customer_bot.py
 (Staff Bot) (Customer Bot)
 │ │
 └──────────┬───────────────┘
 ▼
 api_server.js
 (Node.js Express, Port 3000)
 │
 ┌───────┴────────┐
 ▼ ▼
 bookings.json Google Sheets
 waitlist.json (Primary DB)
```

**3 services running together:**
- `main.py` — Staff bot (systemd: psvibe-bot)
- `customer_bot.py` — Customer bot (systemd: psvibe-customer)
- `api_server.js` — API server (systemd: psvibe-api, port 3000)
- Caddy reverse proxy: `ps-vibe.com/api/*` → port 3000

---

## 2. Staff Bot (main.py) — Architecture

### 2.1 Entry Point & Startup
```python
if __name__ == "__main__":
 1. pgrep -f "python3 main.py" → kill old processes
 2. Write PID to /tmp/ps_vibe_bot.lock
 3. ensure_sheet_headers() — check Google Sheets column headers
 4. keep_alive() — HTTP server (skipped on VPS)
 5. asyncio.new_event_loop() → main() in loop
 6. On crash: wait 5s, restart
```

### 2.2 Conversation State Machine
Single large ConversationHandler with integer state constants (100+ states).
Flow: User message → ConversationHandler → state handler → returns next state or END

### 2.3 Button System
- **BTN_ Constants** — string constants for ReplyKeyboard
- **InlineKeyboard** — callback buttons with pattern matching

### 2.4 Staff Bot → API Calls
Staff bot calls API server via `_replit_get()`, `_replit_post()`, `_replit_patch()`:

```python
_API_KEY = ***"API_KEY", "")
def _api_base() -> str:
    return os.environ.get("API_BASE_URL", "").rstrip("/")
    # Value: "https://ps-vibe.com"

def _replit_get(path: str, timeout: int = 30):
    # GET https://ps-vibe.com/api/{path}
    # Header: X-API-Key: ***
```

**API call locations:**
| Function | API Call | Purpose |
|---|---|---|
| `cmd_inventory` | GET `sheets/inventory` | Stock status |
| `cmd_today_report` | GET `sheets/report-data` | Daily report batch |
| `cmd_today_report` | GET `sheets/staff-breakdown` | Staff KPI |
| `cmd_weekly_report` | GET `sheets/weekly-report` | Weekly summary |
| `cmd_weekly_report` | GET `sheets/pnl?m=...` | P&L data |
| `cmd_console_status` | GET `sheets/consoles` | Console live status |
| `cmd_admin_bookings` | GET `bookings?status=*` | Booking lists |
| `cmd_staff_booking` | POST `bookings` | Create booking |
| `step_bk_approve` | GET `bookings/{id}` + GET `sheets/consoles` | Booking details |
| `save_receipt_json` | POST `api/receipt` | Save receipt |
| `cmd_financial_report` | GET `finance/*` | All finance endpoints |
| `step_end_session` | POST `waitlist/notify` | Notify next in waitlist |

### 2.5 Cache System
In-memory cache to avoid Google Sheets quota:
- `_CFG` — Config cache (5 min TTL)
- `_MBR_ROWS` — Member rows (3 min TTL)
- `_BK_ROWS` — Booking rows (30s TTL)
- `_GAME_ROWS` — Game library (10 min TTL)
- `_bg_cache_refresh` background task: every 5 min

### 2.6 Session Reminder System
Two parallel reminder systems:
1. **In-process asyncio task** (`_remind_loop`): 5 min before end, repeats every 5 min
2. **n8n webhook**: restart-proof, POST to N8N_SESSION_WEBHOOK

---

## 3. Customer Bot (customer_bot.py) — Architecture

### 3.1 API Helpers
```python
API_BASE = os.environ.get("API_BASE_URL", "")  # "https://ps-vibe.com"
_API_KEY = ***"API_KEY", "")
def _api_get(path: str): ...
def _api_post(path: str, body: dict): ...
def _api_patch(path: str, body: dict): ...
def _api_delete(path: str): ...
```

### 3.2 Features
- **Booking Flow**: /book → member/guest check → date/time → console → duration → game → confirm
- **My Bookings**: /mybookings → active + past bookings
- **Balance Check**: /balance → member balance by rank
- **Console Status**: /today or /status → live console availability
- **Waitlist**: /waitlist → join/leave waitlist
- **AI Free Chat**: Gemini AI for natural conversation + function calling

---

## 4. API Server (api_server.js) — Architecture

### 4.1 Endpoint Groups
- **Receipts**: POST `/api/receipt`, GET `/api/receipt/:id`
- **Sheets Read (GET)**: config, summary, members, inventory, report-data, consoles, pnl, etc.
- **Sheets Write**: promotions, bookings, payroll, log
- **Bookings (JSON store)**: CRUD on bookings.json
- **Waitlist (JSON store)**: CRUD on waitlist.json
- **Finance**: shareholders, assets, depreciation, accounts, pnl, balance-sheet, etc.
- **Bot Users**: track, get user, feedback, session-end-notify
- **Members**: extra data, birthday, referral, streak, history
- **Cache**: invalidate, list, ack

### 4.2 Security Middleware
1. Security Headers (nosniff, DENY, XSS)
2. CORS (ps-vibe.com, localhost)
3. requireApiKey (except public: GET receipt/:id, GET healthz)

### 4.3 Data Storage
- **Google Sheets** (primary): Sales_Daily, Card_Wallet, TopUp_Log, Console_Booking, Setting, etc.
- **JSON Files** (fast, no quota): bookings.json, waitlist.json
- **Write Lock**: `_withBkLock` to prevent race conditions

### 4.4 API Server Cache
```javascript
const _cache = new Map();  // { key: { data, expiresAt } }
// TTLs: config=5min, members=3min, inventory=2min, consoles=30s
```

---

## 5. Booking Status Flow
```
pending → confirmed → arrived → completed
                         ↓ (if cancelled)
                      cancelled
```

---

## 6. Top-Up Flow (Staff Bot)
```
/topup → Member ID → Amount → KPay/Cash → Confirm
→ Google Sheets: TopUp_Log append, Card_Wallet H/E/F/G update
→ save_receipt_json()
```

---

## 7. Data Flow Summary
- **Staff Bot**: Direct gspread writes + API calls for reads
- **Customer Bot**: All API calls via api_server.js
- **API Server**: Google Sheets (googleapis) + JSON files + Telegram direct
- **n8n**: Webhook-based reminders, scheduled reports, server status checks
