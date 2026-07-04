# AKT Clothing Shop ERP — Project State

**Created:** 2026-07-04
**Priority:** Side Project
**Status:** 🟢 Development Complete (v1.0)
**Maintained By:** Kora (Boss's friend uses only)

## Tech Stack
- Backend: Python FastAPI (port 8010)
- Database: MySQL 8.0 (akt_clothing)
- Frontend: Vue 3 + Vite + Tailwind CSS (port 5173)
- Charts: Chart.js + vue-chartjs
- Auth: JWT

## Current Features
- ✅ Product Management (CRUD + size/color variants + barcode)
- ✅ Sales POS (barcode search, discount, multi-payment, credit, void)
- ✅ Purchase Management (GRN, supplier, stock auto-increment)
- ✅ Customer Credit System (ledger, payment recording)
- ✅ Supplier Management
- ✅ Reports (Dashboard, P&L, Stock Balance, Top Products)
- ✅ Settings (shop info, invoice prefix)
- ✅ Auth (JWT login, single admin user)

## Default Login
- Username: admin
- Password: admin123

## Database
- 13 tables (products, product_variants, categories, suppliers, customers, 
  purchases, purchase_items, sales, sale_items, credit_payments, 
  stock_movements, shop_settings, users)
- Full stock movement audit trail

## Deployment
- Backend: /opt/kora-projects/akt_clothing/code/backend/
- Frontend: /opt/kora-projects/akt_clothing/code/frontend/
- Config: /opt/kora-projects/akt_clothing/config/

## Known Issues
- None (v1.0 just built, not yet deployed)

## Next Steps
- Deploy to VPS
- Import initial product data
- Test end-to-end flow
