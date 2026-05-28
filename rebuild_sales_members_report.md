# Rebuild Report: Sales + Members Handlers

**Date:** 2026-05-27 04:31 UTC  
**Task:** Rebuild review of `sales.py`, `members.py`, `referral.py`, `discount.py`

---

## ✅ Files Reviewed & Deployed

| File | Lines | Status |
|------|-------|--------|
| `sales.py` | 1,273 | ✅ Clean — no fixes needed |
| `members.py` | 1,137 | ✅ Clean — no fixes needed |
| `referral.py` | 135 | 🔧 Fixed — added missing imports |
| `discount.py` | 435 | 🔧 Fixed — added missing imports |

---

## 🔧 Fixes Applied

### `referral.py`
- **Missing `from bot import *`** — Required to access `fetch_referral_code()`, `fetch_members()`, `save_referral_code()`, `member_sh`, `cmd_cancel()`, `show_mm_menu()`, `prompt_mm_lookup()`, and all constants (`BTN_BACK_MAIN`, `BTN_BACK`, `BTN_CANCEL`, `MM_MENU`, `REFERRAL_CODE`)
- **Missing `import asyncio`** — Used by `asyncio.get_event_loop().run_in_executor()` for `save_referral_code()`

### `discount.py`
- **Missing `from bot import *`** — Required to access `fetch_base_rate()`, `fetch_promotions_cached()`, `cmd_cancel()`, `prompt_kpay()`, `prompt_confirm()`, and all constants (`BTN_PROMO_APPLY`, `BTN_MANUAL_DISC`, `BTN_SKIP_DISC`, `NAV_ROW`, `BTN_BACK`, `BTN_CANCEL`, `DISCOUNT`, `PROMO_SELECT`, `BUNDLE_FOC`)
- **Missing `import asyncio`** — Used by `asyncio.to_thread(fetch_promotions_cached)`

---

## ✅ V1/V2 API Verification

Compared all bot-level function calls against V1 (`/root/staging/monolithic_ref/main.py`):

| Function | V1 Match | Notes |
|----------|----------|-------|
| `fetch_base_rate` | ✅ | Same signature: `def fetch_base_rate() -> int` |
| `fetch_console_multiplier` | ✅ | `def fetch_console_multiplier(console_id: str) -> float` |
| `fetch_console_status` | ✅ | `def fetch_console_status() -> list[dict]` |
| `fetch_member_data` | ✅ | Returns dict with name, phone, email, net_spend, rank_raw, wallet_mins |
| `display_rank` | ✅ | `def display_rank(rank) -> str` — normalizes "New Member" to "Warrior" |
| `rank_emoji` | ✅ | `def rank_emoji(rank) -> str` — returns emoji by rank |
| `step_hdr` | ✅ | `def step_hdr(step, total, label) -> str` |
| `fetch_referral_code` | ❌ NOT in V1 | New V2 function only |
| `save_referral_code` | ❌ NOT in V1 | New V2 function only |
| `fetch_promotions_cached` | ❌ NOT in V1 | New V2 function only |

The 3 functions not found in V1 are V2-specific additions — they exist in the refactored `bot/` package.

---

## 🟢 Post-Deploy Status

| Check | Result |
|-------|--------|
| Syntax check (all 4 files) | ✅ All pass |
| File deployment (rsync) | ✅ All copied |
| Service restart | ✅ `systemctl restart psvibe-bot-refactored.service` |
| Service active | ✅ `active` |
| Bot startup log | ✅ `PS Vibe Bot is running...` |
| No import errors on startup | ✅ Clean boot |

---

## ⚠️ Note: Pre-existing Issue

A `NameError: name 'show_game_menu' is not defined` appeared in logs from the **previous** bot process (before restart). This is in `console.py` and was **not** introduced by this deployment — it's a pre-existing issue unrelated to sales/members/referral/discount.
