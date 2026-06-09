# Fix File Permissions — chmod Remediation

**VPS:** 5.223.81.16  
**Date:** 2026-05-28 12:39 UTC  
**Scope:** `/root/psvibe-sale-bot/`

## Results

### S-3: Sensitive File — `service_account.json`

| Before | After | Status |
|--------|-------|--------|
| world-readable (likely 644) | `-rw-------` (600) | ✅ Fixed |

### S-4: World-Writable Python Files

| File | Before | After | Status |
|------|--------|-------|--------|
| `bot/handlers/analytics.py` | o+w | 644 | ✅ Fixed |
| `bot/report_generator.py` | o+w | 644 | ✅ Fixed |
| `send_daily_report.py` | o+w | 644 | ✅ Fixed |
| `bot/handlers/dashboard_bot.py` | N/A | N/A | ⚠️ File not found (skip) |

## Verification

- **World-writable `.py` files remaining:** 0 ✅
- **World-writable `.json` files remaining:** 0 ✅
- **World-readable `secret*.json`:** 0 ✅

## Commands Run

```bash
chmod 600 /root/psvibe-sale-bot/service_account.json
chmod 644 /root/psvibe-sale-bot/bot/handlers/analytics.py
chmod 644 /root/psvibe-sale-bot/bot/report_generator.py
chmod 644 /root/psvibe-sale-bot/send_daily_report.py
```

All issues resolved. No remaining world-readable sensitive files or world-writable Python files detected.
