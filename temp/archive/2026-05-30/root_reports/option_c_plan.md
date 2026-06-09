# Option C Implementation Plan — MySQL Full Integration
# For PS VIBE - PS5 Gaming Lounge

## Architecture Change

### Current (BEFORE - Option C):
- Bots → gspread (direct Google Sheets API) → 429 Rate Limit errors
- MySQL Docker = orphaned (has data but no code uses it)

### Target (AFTER - Option C):
- Bots → API Server (FastAPI on port 8000) → MySQL (primary)
- API Server → gspread (sync layer only, periodic)
- Zero direct gspread calls from bots

## Implementation Steps

### Step 1: API Server — MySQL Integration (db_client.py)
- Add mysql-connector-python to requirements
- Create /root/psvibe_api_server/db_client.py
  - Read from MySQL (psvibe_api database)
  - Auto-sync from Sheets on cache miss
  - Connection pooling
- Create /root/psvibe_api_server/sync_service.py
  - Periodic sync: Sheets → MySQL (every 5 min)
  - Manual sync endpoint: POST /api/sync

### Step 2: API Server — Update Routes to Use MySQL
- Update app.py routes to read from MySQL first
- Fallback to gspread if MySQL data is stale
- Returns: MySQL data (fast, no rate limits)

### Step 3: Bot .env Updates
- Sales Bot: API_BASE_URL=http://localhost:8000 (already fixed ✅)
- Customer Bot: API_BASE_URL=http://localhost:8000
- Wallet Bot: API_BASE_URL=http://localhost:8000

### Step 4: Deploy & Test
- Restart API server
- Verify MySQL reads
- Verify no 429 errors
