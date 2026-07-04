# AKT Clothing Shop ERP — Project State

**Created:** 2026-07-04
**Priority:** Side Project
**Status:** 🟢 Deployed & Active (v1.2)
**Maintained By:** Kora (Boss's friend ArKarThant uses)

## Tech Stack
- Backend: Python FastAPI (port 8010, systemd: akt-clothing-api)
- Database: MySQL 8.0 (akt_clothing)
- Frontend: Vue 3 + Vite + Tailwind CSS
- Charts: Chart.js + vue-chartjs
- Auth: JWT

## Current Features
- ✅ Product Management (CRUD + size/color variants + barcode + **image upload**)
- ✅ Sales POS (barcode search, discount, multi-payment, credit, void, FIFO costing)
- ✅ Purchase Management (GRN, supplier required, stock auto-increment, split payment)
- ✅ Customer Credit System (ledger, payment recording, R/P page)
- ✅ Supplier Management
- ✅ Payment Accounts (Cash Register, KPay, WavePay, Bank — dynamic balance)
- ✅ Reports (Dashboard, P&L, Stock Balance, Top Products)
- ✅ Settings (shop info, invoice prefix, low stock threshold — apply site-wide)
- ✅ Auth (JWT login, single admin user)
- ✅ Printable Sales Receipt (HTML, print-ready)
- ✅ Logo + Favicon (BKK Fashion Shop branding)
- ✅ Product Image Upload (+ preview in form & table)
- ✅ Mobile Responsive (hamburger sidebar, scrollable tables)

## Login
- Username: ArKarThant
- Password: AKTBKKClothing2026
- URL: http://ps-vibe.com/akt-clothing-shop/

## Database
- 15+ tables (products, product_variants, categories, suppliers, customers,
  purchases, purchase_items, sales, sale_items, credit_payments,
  stock_movements, inventory_lots, payment_accounts, payment_transactions,
  shop_settings, users)
- Full stock movement audit trail (FIFO inventory costing)
- Payment account balances auto-tracked via payment_transactions

## Deployment
- Backend: /opt/kora-projects/akt_clothing/code/backend/
- Frontend: /opt/kora-projects/akt_clothing/code/frontend/ (built → static/)
- Config: /opt/kora-projects/akt_clothing/config/.env
- Served via: PS VIBE API proxy → Cloudflare Tunnel → ps-vibe.com
- Proxy route: /akt-clothing-shop/* → localhost:8010
- Upload dir: /opt/kora-projects/akt_clothing/code/static/uploads/products/

## 2026-07-04 Fixes Applied
- [x] Account Balance bug (name mapping + type fallback)
- [x] Add Product crash (empty string → None validator)
- [x] Sale Customer link visibility (always show, backend enforce)
- [x] Purchase UX (split/payment single input mode)
- [x] Payment account balance drift (balance auto-sync)
- [x] Old transaction backfill (sales #2, #3 payment_transactions)
- [x] Logout race condition (401 interceptor + clean break)
- [x] Favicon added (BKK Fashion Shop logo)
- [x] Product image upload (multipart API + preview)

## Known Issues
- None (all reported bugs fixed)

## Next Steps
- (awaiting Boss/ArKarThant feedback)
