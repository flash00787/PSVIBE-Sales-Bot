
## 2026-06-03 19:12 UTC — Bug Fix: Coupon Gen + Promo List Field Mapping

### Bug 1: Coupon Code Not Generating (console.py)
**Root cause:** Double-unwrap of API response. `_replit_get_async` and `_replit_post_async` both call `_api_call_async` which already strips the `{success:true, data:...}` envelope. The coupon generation code was doing an additional `.get("data")` on the already-unwrapped result, yielding `None`.

**Fix:** Removed `.get("data")` from:
- `promo_data = promo_resp` (was `promo_resp.get("data") if isinstance(...)`)
- `gen_data = gen_resp` (was `gen_resp.get("data") if isinstance(...)`)

Also removed broken import of non-existent `api_generate_coupon` from `bot.api_client`.

### Bug 2: Wallet Balance Deduction (sales.py)
**Status:** Already implemented correctly. The wallet deduction code in `step_sale_confirm` (lines 1343-1366) properly:
1. Deducts from GSheet (primary) 
2. Calls `_replit_post("wallet/deduct", ...)` for MySQL sync
3. Has proper error handling with `try/except`

The API endpoint `POST /api/wallet/deduct` in app.py is operational.

### Bug 3: Promotion List Empty/Error
**Root cause:** API returns MySQL column names (`promo_name`, `discount_type`, `discount_value`) but the discount handler expects different field names (`title`, `type`, `discount_percent`). All promotions showed with blank titles.

**Fix in `fetch_promotions_cached()` (bot/__init__.py):**
Added field normalization mapping:
- `promo_name` to `title`
- `discount_type` to `type`
- `discount_value` to `discount_percent`

### Files Modified:
- `/root/psvibe-sales-bot/bot/handlers/console.py` — lines 305, 311, 320
- `/root/psvibe-sales-bot/bot/__init__.py` — `fetch_promotions_cached()` (lines 1984-2001)

### Verification:
- All Python files compile clean
- API server running on port 8000
- Sale bot running clean
- Promotions API returns valid data
- Wallet deduct endpoint operational
