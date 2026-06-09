# API Smoke Test Results
**Date:** 2026-05-28 12:01:55 UTC
**Server:** 5.223.81.16:8000
**Total endpoints tested:** 45

## ✅ Working (200) — 29 endpoints
- GET health
- GET fetch_console_status
- GET fetch_members
- GET fetch_staff
- GET fetch_staff_names
- GET fetch_food_prices
- GET fetch_food_costs
- GET fetch_games
- GET fetch_game_library
- GET fetch_console_games
- GET fetch_base_rate
- GET fetch_new_member_defaults
- GET fetch_rank_thresholds
- GET fetch_bonus_table
- GET fetch_rank_table_display
- GET fetch_alltime_effective_rate
- GET fetch_base_salaries
- GET fetch_promotions_cached
- GET fetch_allowed_staff_ids
- GET next_voucher
- GET next_member_id
- GET next_member_row_no
- GET sheets/config
- GET analytics/member_activity
- GET analytics/console_usage
- GET mysql/health
- GET mysql/sync_status
- GET get_games_on_console/PS5
- POST create_booking

## ❌ Broken (4xx/5xx) — 16 endpoints
- GET fetch_consoles_with_game → 404
  Body: {"detail":"Not Found"}

- GET analytics/dashboard → 500

- GET analytics/daily_sales → 500

- GET analytics/topups → 500

- GET analytics/weekly_trends → 500

- GET fetch_member_data/1 → 404
  Body: {"detail":"Member 1 not found"}

- GET fetch_wallet_mins/1 → 404
  Body: {"detail":"Member 1 not found"}

- GET fetch_balance_mins/1 → 500
  Body: {"detail":"Member 1 not found"}

- GET fetch_member_tier/1 → 404
  Body: {"detail":"Member 1 not found"}

- GET fetch_console_multiplier/PS5 → 500

- GET fetch_member_effective_rate/1 → 404
  Body: {"detail":"Member 1 not found"}

- GET fetch_referral_code/1 → 404
  Body: {"detail":"Member 1 not found"}

- GET end_booking/1 → 405
  Body: {"detail":"Method Not Allowed"}

- GET cancel_booking/1 → 405
  Body: {"detail":"Method Not Allowed"}

- GET remove_console_from_setting/1 → 405
  Body: {"detail":"Method Not Allowed"}

- POST save_attendance → 500

## Notes
- All tests used API key: JWIErd82...
- POST endpoints tested with empty JSON body: create_booking, save_attendance
- Timeout: 15s per endpoint
