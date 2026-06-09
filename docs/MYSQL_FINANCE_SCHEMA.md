# MySQL Finance Schema — PS VIBE

## Database: `psvibe_api` (Docker: psvibe-mysql)

### 1. finance_opex_log — Operational Expenses
| Field | Type | Description |
|-------|------|-------------|
| id | INT (PK, auto) | Record ID |
| date | DATE | Expense date |
| category | VARCHAR(100) | Category (e.g. utilities, rent) |
| amount | DECIMAL(15,2) | Amount in MMK |
| description | TEXT | Details |
| created_at | TIMESTAMP | Auto-logged |

**Sample:** ✅ 12 records synced, 10ms response

### 2. finance_assets — Fixed Assets
| Field | Type | Description |
|-------|------|-------------|
| id | INT (PK, auto) | Record ID |
| name | VARCHAR(200) | Asset name |
| purchase_date | DATE | Purchase date |
| amount | DECIMAL(15,2) | Purchase amount |
| notes | TEXT | Additional info |
| created_at | TIMESTAMP | Auto-logged |

**Sample:** ✅ 56 records synced, 10ms response

### 3. finance_prepaid — Prepaid Expenses
| Field | Type | Description |
|-------|------|-------------|
| id | INT (PK, auto) | Record ID |
| description | VARCHAR(200) | Prepaid item |
| amount | DECIMAL(15,2) | Amount |
| settle_date | DATE | Expected settlement |
| status | VARCHAR(20) | pending / settled |
| created_at | TIMESTAMP | Auto-logged |

### 4. finance_payables — Accounts Payable
| Field | Type | Description |
|-------|------|-------------|
| id | INT (PK, auto) | Record ID |
| payee | VARCHAR(200) | Payee name |
| amount | DECIMAL(15,2) | Amount owed |
| due_date | DATE | Due date |
| status | VARCHAR(20) | pending / paid |
| created_at | TIMESTAMP | Auto-logged |

### 5. finance_receivables — Accounts Receivable
| Field | Type | Description |
|-------|------|-------------|
| id | INT (PK, auto) | Record ID |
| payer | VARCHAR(200) | Payer name |
| amount | DECIMAL(15,2) | Amount due |
| due_date | DATE | Due date |
| status | VARCHAR(20) | pending / received |
| created_at | TIMESTAMP | Auto-logged |

### 6. finance_advances — Salary Advances
| Field | Type | Description |
|-------|------|-------------|
| id | INT (PK, auto) | Record ID |
| member_id | VARCHAR(50) | Staff member ID |
| amount | DECIMAL(15,2) | Advance amount |
| advance_date | DATE | Date advanced |
| settle_date | DATE | Expected repayment |
| status | VARCHAR(20) | pending / settled |
| notes | TEXT | Additional info |
| created_at | TIMESTAMP | Auto-logged |

---

## API Endpoints

### GET (Read)
| Endpoint | Description |
|----------|-------------|
| `/api/finance/opex` | List all opex records |
| `/api/finance/assets` | List all assets |
| `/api/finance/prepaid` | List all prepaid |
| `/api/finance/payables` | List all payables |
| `/api/finance/receivables` | List all receivables |
| `/api/finance/advances` | List all advances |

### PUT (Update)
| Endpoint | Description |
|----------|-------------|
| `/api/finance/assets/{id}` | Update asset |
| `/api/finance/payables/{id}` | Update payable |
| `/api/finance/receivables/{id}` | Update receivable |

### POST (Create)
POST endpoints for all 6 tables exist via `app.py` (add/append operations)

---

## Connection
- **Host:** localhost (Docker bridge)
- **Port:** 3306
- **User:** `psvibe_user` | **Root:** `root`
- **Password:** In `/etc/psvibe/secrets.env`
- **Auth Method:** API Server at port 8000 (bot → API → MySQL)

## Data Flow
```
Bot (Python) → API (FastAPI :8000) → MySQL (Docker :3306) → gspread (cold fallback)
```
