# PS VIBE Bot V2 Rebuild Plan

## Current Problem
V2 refactored code has API layer (in bot/__init__.py) but handlers use `from bot.handlers import *` which doesn't re-export API functions (`_replit_get`, `_replit_post`, `_replit_patch`). This causes NameError at runtime when handlers try to call API.

## Strategy: Take V2 Framework, Rebuild Logic from V1

**V2 Framework to Keep:**
- Package structure (bot/, bot/handlers/, app.py)
- main.py entry point
- keep_alive.py
- Telegram bot setup (Application, ConversationHandler)
- Google Sheets connection helpers (sh orth, get/set)
- Cache system (_load_cfg, _load_members, _bg_cache_refresh)
- BTN constants
- BotState enum

**Rebuild from V1:**
- API functions (_replit_get, _replit_post, _replit_patch) — but properly integrated into handler import chain
- All handler functions — with proper API imports
- All data fetcher functions
- Business logic in each handler

## Phases

### Phase 1: Documentation (NOW)
- Extract V1's API layer and document
- Extract V1's handler function logic per domain
- Save as MD files

### Phase 2: Core Framework Fix
- Fix bot/__init__.py to properly re-export API functions via handlers/__init__.py
- Ensure all helpers are accessible both via `from bot import *` AND `from bot.handlers import *`

### Phase 3: Handler Rebuild (one by one)
1. main_menu.py — menu buttons, navigation
2. commands.py — start, cancel, help
3. sales.py — daily sales flow (7-step wizard)
4. members.py — member management, lookup, new member
5. booking.py — staff booking
6. booking_flow.py — session management
7. console.py — console status, end session
8. reports.py — inventory, today report, weekly report
9. admin.py — admin panel
10. admin_bookings.py — booking approval
11. attendance.py — staff attendance
12. finance.py — financial reports
13. games.py — game library management
14. ginst.py — game installation
15. payroll.py — payroll calculation
16. referral.py — referral codes
17. salary_adv.py — salary advances
18. ssd_disc.py — SSD discount
19. discount.py — discount management
20. stock.py / stock_in.py — stock management
21. notify.py — notifications
22. waitlist.py — waitlist management
23. broadcast.py — broadcast
24. console_mgmt.py — console management
25. help.py — help/version

### Phase 4: Test & Deploy (per handler)
- syntax check
- import test
- deploy via rsync
- restart service
- verify log
