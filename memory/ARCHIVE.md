# Archived Memory Entries
*Archived: 2026-06-09 05:49 UTC*

(dedup) psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅ | psvibe-dashboard ✅
  (dedup) - psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅
  (dedup) - 4. Checked coupon generation in `step_sale_confirm` → calls `api_post` from `bot/api_client.py`, which uses `?api_key=` query param (fails with 401)
  (dedup) - 1. **`api_client.py` `api_post()`** uses `?api_key=` query param → 401 response → coupon generation silently fails
  (dedup) - 2. **`api_client.py` `api_get()`** also uses `?api_key=` query param → would fail on any GET
  (dedup) - psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅
  (dedup) - psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅
  (dedup) - "book_value": float(a.get("book_value", 0) or 0) or (float(a.get("amount", 0) or 0) - float(...))
  (dedup) - psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅ | psvibe-dashboard ✅
  (dedup) - `net_position = assets_total - advances_pending - prepaid_total`
  (dedup) - ✅ Services: psvibe-api ✅, psvibe_customer_bot ✅, psvibe-sale-bot ✅
  (dedup) - psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅ | psvibe-dashboard ✅
  (dedup) - **Total Monthly Dep:** 4,029,826 Ks | **Total Acc. Dep:** 3,262,283 Ks

# Archived Memory Entries
*Archived: 2026-06-10 04:37 UTC*

(dedup) 9. **Python `.pyc` cache stale after edit:** Always `find -name '__pycache__' -exec rm -rf {} +` then restart

# Archived Memory Entries
*Archived: 2026-06-10 16:38 UTC*

(dedup) - psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅ | psvibe-dashboard ✅
