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

# Archived Memory Entries
*Archived: 2026-06-11 15:31 UTC*

(dedup) - Knowledge graph: ✅ 54 nodes, 1418 edges
  (dedup) - Knowledge graph: ✅ 54 nodes, 1418 edges
  (dedup) - Stale lock cleanup: ✅ 0 cleaned
  (dedup) - 1. 📅 Real Booking Schedule (9AM-9PM timeline, color-coded)
  (dedup) - 2. 💰 Real Sales Chart (7-day Canvas bar chart)
  (dedup) - 3. 🔍 Member Quick Lookup (search + wallet balance)
  (dedup) - 4. ⚠️ Smart Alerts Panel (health alerts)
  (dedup) - 5. 📦 Food Stock Status (menu + stock levels)
  (dedup) - 6. 📊 End-of-Day Summary (today's panel)
  (dedup) - 9. ⚡ Quick Commands (Health, Docker, Uptime, Backups)
  (dedup) - **MEMORY.md truncation:** Session context loads ~11KB of ~40KB file. Keep MEMORY.md ≤20KB — use module files for details
