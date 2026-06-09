# PS VIBE Bot Code Analysis Context

## Repository
- Path: `/root/psvibe-sales-bot/` on VPS `5.223.81.16` (SSH as root)
- SSH Key: `/home/node/.openclaw/workspace/.ssh/id_rsa`
- Services: `psvibe-sale-bot`, `psvibe_customer_bot`, `psvibe-api`, `psvibe-watchdog`
- Quality Score: 90/100 (EXCELLENT)
- 1 orphan state: `_CGAME_TS`

## Key File Sizes
```
523  bot/app.py
2866 bot/__init__.py
1425 bot/handlers/members.py
512  bot/handlers/admin.py
131  bot/handlers/main_menu.py
196  bot/constants.py
842  bot/api_client.py
894  customer_bot/handlers.py
257  customer_bot/main.py
612  customer_bot/api.py
1393 customer_bot/booking_handlers.py
```

## Sale Bot Files
```
bot/app.py                 - Main entry, route mapping, ConversationHandlers
bot/__init__.py            - BotState ENUM (68 states), __all__, shared imports
bot/constants.py           - Button labels, constants
bot/api_client.py          - API client calls
bot/helpers.py             - Helper functions
bot/handlers/admin.py      - Admin panel
bot/handlers/admin_bookings.py - Admin bookings
bot/handlers/attendance.py - Attendance tracking
bot/handlers/booking_flow.py - Booking flow
bot/handlers/booking.py    - Booking management
bot/handlers/broadcast.py  - Broadcast messages
bot/handlers/commands.py   - Bot commands
bot/handlers/console_mgmt.py - Console management
bot/handlers/console.py    - Console display
bot/handlers/discount.py   - Discount handling
bot/handlers/finance.py    - Finance reports
bot/handlers/games.py      - Games library
bot/handlers/ginst.py      - G-Inst (installation)
bot/handlers/help.py       - Help menu
bot/handlers/__init__.py   - Handler imports
bot/handlers/input_logger.py - Input logging
bot/handlers/main_menu.py  - Main menu
bot/handlers/members.py    - Member management (Top Up, New Member)
bot/handlers/notify.py     - Notifications
bot/handlers/payroll.py    - Payroll
bot/handlers/referral.py   - Referral system
bot/handlers/reports.py    - Reports
bot/handlers/salary_adv.py - Salary advance
bot/handlers/sales.py      - Sales tracking
bot/handlers/ssd_disc.py   - SSD discount
bot/handlers/stock_in.py   - Stock in
bot/handlers/stock.py      - Stock management
bot/handlers/waitlist.py   - Waitlist
```

## Customer Bot Files
```
customer_bot/main.py         - 257 lines - Entry point, handlers mapping
customer_bot/handlers.py     - 894 lines - All customer handlers
customer_bot/api.py          - 612 lines - API calls
customer_bot/booking_handlers.py - 1393 lines - Booking flow (ConversationHandler)
customer_bot/booking.py      - Booking helpers
customer_bot/__init__.py     - Imports
customer_bot/ai.py           - AI features
customer_bot/data/faq.py     - FAQ data
customer_bot/data/games.py   - Games data
customer_bot/data/prompts.py - AI prompts
customer_bot/data/time_utils.py - Time utilities
```

## Known Issues (Pre-existing)
1. Top Up Payment flow was recently fixed (dead code bug)
2. Console ID URL encoding not fixed (spaces in "C - 01")
3. 1 orphan state: `_CGAME_TS`
4. Customer bot has booking ConversationHandler with 7 text-accepting states
