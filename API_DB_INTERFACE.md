# Shared Interface: API ↔ Database ↔ Bot

**Date:** 2026-05-27
**Purpose:** Define the shared function signatures that API agent and Database agent must implement for the PS VIBE V2 bot.

---

## Core Convention

The V2 bot's `_replit_*` functions call an API server at `_api_base() + "/api/" + path`.
Both agents MUST implement the exact same path/function naming so they match.

---

## API Endpoints Required by Bot

### Sheets Endpoints
```
GET  /api/sheets/promotions           → list[dict] — active promotions
GET  /api/sheets/config               → dict — Setting sheet config
GET  /api/sheets/inventory            → list[dict] — inventory items
     ?nocache=1 → force cache refresh
GET  /api/sheets/consoles             → list[dict] — console list
GET  /api/sheets/pnl                  → dict — P&L data
GET  /api/sheets/report-data          → dict — today/period report
GET  /api/sheets/staff-breakdown      → list[dict] — staff sales breakdown
POST /api/sheets/promotions-log       → create promotion usage record
```

### Booking Endpoints
```
GET  /api/bookings                    → list[dict] — all bookings
     ?status=pending|confirmed        → filtered by status
     ?memberId={id}                   → filtered by member
POST /api/bookings                    → create new booking
GET  /api/bookings/{id}               → get single booking
PATCH /api/bookings/{id}/status       → update booking status
     body: { "status": "confirmed"|"done"|"cancelled" }
GET  /api/bookings/broadcast-targets  → list of broadcast recipients
```

### Waitlist Endpoints
```
POST /api/waitlist/notify             → notify next waiting customer
     body: { "console_id": "C-01" }
```

### Finance Endpoints
```
GET  /api/finance/pnl?m={month}       → monthly P&L report
GET  /api/finance/balance-sheet       → current balance sheet
GET  /api/finance/accounts            → chart of accounts
GET  /api/finance/depreciation?year={y} → depreciation schedule
GET  /api/finance/profit-sharing?m={m}  → profit sharing for month
POST /api/finance/setup-sheets        → create finance sheet structure
```

### Receipt Endpoints
```
POST /api/receipt                     → push receipt data
     headers: { "x-receipt-secret": "...", "X-API-Key": "..." }
GET  /api/receipt/{voucher_id}        → get receipt data (public URL)
```

---

## Auth Convention

All endpoints require header: `X-API-Key: {API_KEY}`
Receipt endpoint additionally requires: `x-receipt-secret: {SECRET}`

---

## Response Format Convention

### Success
```json
{
  "status": "ok",
  "data": [ ... ]   // or { ... }
}
```

### Error
```json
{
  "status": "error",
  "message": "description"
}
```

### Conflict (HTTP 409)
```json
{
  "error": "booking conflict",
  "__status__": 409
}
```

---

## Database Layer (Database Agent)

Database Agent must provide storage for:
1. **Config cache** — Setting sheet rows cached locally
2. **Inventory cache** — Inventory items cached locally
3. **Booking records** — Console_Booking sheet data accessible via SQL
4. **Promotions cache** — Active promotions
5. **Finance reports** — Pre-computed P&L, balance sheet
6. **Receipt storage** — Receipt JSON locally

Database agent function signatures MUST MATCH the same paths as API endpoints above.
When API agent receives a request, it calls Database agent functions internally.

---

## Implementation Guidance

### API Agent
- Build a lightweight web server (FastAPI or Flask)
- Listen on port 8000 (or env-configured)
- Set `API_BASE_URL` env var or write to `/etc/environment`
- Each endpoint handler calls Database agent's matching function
- Must handle CORS, logging, error responses

### Database Agent
- Use SQLite (file-based, no extra process needed)
- Or use Redis for caching layer
- SQLite path: `/root/psvibe-sale-bot/bot_data.db`
- Implement functions: `sheets_get_promotions()`, `sheets_get_config()`, `bookings_list()`, `bookings_get(id)`, `bookings_create(data)`, etc.
- All functions return dict or list (JSON-serializable)
