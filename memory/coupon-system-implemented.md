# CashBack Coupon System — Implementation Summary

> **Date:** 2026-06-02 | **Grand Opening:** June 6-7, 2026

## Status: ✅ COMPLETE

### DB Tables (MySQL: psvibe_api)
- **`promotions`** — Promotion definitions (type, dates, coupon expiry)
- **`member_coupons`** — Customer coupon codes with balance tracking

### Config
- `/etc/psvibe/secrets.env` — `CASHBACK_START_DATE=2026-06-06`, `CASHBACK_END_DATE=2026-06-07`, `CASHBACK_COUPON_EXPIRY=2026-07-07`

### API Endpoints (app.py)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/promotions/active` | GET | Check if cashback promo is active |
| `/api/coupons/generate` | POST | Generate coupon for member |
| `/api/coupons/list` | GET | List member's coupons |
| `/api/coupons/validate` | POST | Validate coupon code |
| `/api/coupons/redeem` | POST | Deduct coupon balance |

### Sale Bot Integration
- **Session End → Auto-Generate** (`console.py:step_end_session`): On session end, checks if promo active → generates coupon → notifies customer
- **Discount → Apply Coupon** (`discount.py`): Staff can enter coupon code → validates → applies discount → deducts balance

### Customer Bot Integration
- **`/my_coupons`** command (`handlers.py`): Shows member's coupons with balance & expiry
- Registered in `main.py`

### Git Commits
| Repo | SHA | Message |
|------|-----|---------|
| Sales Bot | `3c3c620` | feat: cashback coupon - sale bot + customer integration |
| Sales Bot | `fd8c56a` | feat: api_post/get helpers + coupon notification |
| Sales Bot | `b05982e` | fix: resolve __init__.py corruption - proper BTN_APPLY_COUPON |
| API Server | `6453440` | (combined with booking fixes) |

## All Features This Session (June 2)
1. ✅ Console Selection During Booking
2. ✅ Time-Slot Restriction (past slots hidden)
3. ✅ Console Selection Fix (ReplyKeyboard) 
4. ✅ Staff Check-In
5. ✅ Auto-Cancel No-Show (15 min)
6. ✅ CashBack Coupon System (100% minute cashback)
