# Coupon Code Bug Fix — 2026-06-05

## Emergency Context
- PS VIBE Grand Opening: June 6, 2026 (TOMORROW)
- Boss tested: Console C-09, 60 mins, 12,000 Ks, Cash payment
- **Telegram receipt showed NO coupon code line**
- Grand Opening 100% CashBack promotion active (June 3-7, 2026)

## Root Cause
**The `not is_guest` guard condition was blocking coupon generation for walk-in (Guest) customers.**

The coupon generation code in `step_sale_confirm()` (line 1176) and `launch_session_sale()` (line 1577) had the condition:
```python
if not is_guest and play_mins > 0 and not d.get("_cashback_coupon"):
```

This meant ONLY registered members got cashback coupons. Guest walk-in customers never got coupons, even though the Grand Opening promotion is meant for ALL customers.

### How we confirmed
1. **API endpoint `/api/coupons/generate` exists and works** — tested successfully, generated coupons #12-14
2. **Bot environment has `API_KEY` set** — confirmed via `/proc/<pid>/environ`
3. **Latest receipt (20260605-699.json)** showed: `"member_id": "0 (Guest)"`, `"is_guest": true`, `"coupon_code": ""` — no coupon generated
4. **No coupon-related WARNING logs** in journalctl — the code path was never reached for guests
5. **API tested with `"member_id": "0 (Guest)"`, `"session_minutes": 60`** → Successfully generated coupon CBKDZG80

## Fix Applied

### File: `/root/psvibe-sales-bot/bot/handlers/sales.py`

**Fix 1 — `step_sale_confirm()` at line 1176:**
```python
# BEFORE:
if not is_guest and play_mins > 0 and not d.get("_cashback_coupon"):

# AFTER:
if play_mins > 0 and not d.get("_cashback_coupon"):
```

**Fix 2 — `launch_session_sale()` at line 1577:**
```python
# BEFORE:
if not is_guest and total_mins > 0 and not context.user_data.get("_cashback_coupon"):

# AFTER:
if total_mins > 0 and not context.user_data.get("_cashback_coupon"):
```

### What was NOT changed
- The API server (`app.py`) — coupon endpoints already exist and work correctly
- The Telegram receipt formatting — coupon_line and _receipt_end already handle guests correctly (wallet_bal_line is empty for guests, which is fine)
- The HTML receipt template — coupon_code is in the JSON but not rendered; minor issue, not related to the Telegram receipt bug

## Verification
1. ✅ Python syntax check passed: `py_compile.compile()` returns OK
2. ✅ Services restarted: psvibe-sale-bot (PID 3605914), psvibe_customer_bot (PID 3606025)
3. ✅ API end-to-end test: generated coupon for "0 (Guest)" — coupon #14 (CBKDZG80, 60 mins)
4. ✅ Both fixes confirmed in running code via grep
5. ✅ New bot process has API_KEY in its environment
6. ✅ Sync completed successfully

## Files Modified
- `/root/psvibe-sales-bot/bot/handlers/sales.py` — 2 lines changed (removed `not is_guest and` guard)
- Backups created:
  - `sales.py.bak-coupon-fix-20260605-052314`
  - `app.py.bak-coupon-fix-20260605-052314` (API not changed, backup for safety)

## Post-Fix Testing
The Boss should test again:
1. Start a new sale as Guest (or member)
2. Select console, set 60 mins, confirm with Cash
3. Verify the Telegram receipt shows:
   - `🎫 *CashBack Coupon:* CBXXXXXX — *60 mins*`
4. Verify the separate coupon message is also sent:
   - `🎫 *100% CashBack Coupon!*`
   - `Code: CBXXXXXX`
   - `Minutes: 60 mins`

## Additional Notes
- Coupons for guests are stored under `member_id: "0 (Guest)"` in the DB
- Each coupon has a unique 8-char code (CB + 6 alphanumeric)
- Expiry: June 30, 2026 (set by promotion config)
- Promotion ID 516: "Grand Opening 100% CashBack"
