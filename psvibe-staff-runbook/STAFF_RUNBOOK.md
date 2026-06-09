# 🎮 PS VIBE - Staff Operations Runbook
**For:** Grand Opening June 6, 2026
**Bot:** Staff Telegram Bot (authorized staff only)
**Time Zone:** MMT (UTC+6:30)

---

## Table of Contents
1. [Quick Commands Reference](#quick-commands-reference)
2. [Main Menu Overview](#main-menu-overview)
3. [Daily Opening Procedure](#daily-opening-procedure)
4. [Daily Closing Procedure](#daily-closing-procedure)
5. [Common Scenarios](#common-scenarios)
6. [Admin Panel](#admin-panel)
7. [Finance Management](#finance-management)
8. [Tips & Troubleshooting](#tips--troubleshooting)

---

## Quick Commands Reference

| Command | Description | Who Can Use |
|---------|-------------|-------------|
| `/start` or `/menu` | 🏠 Main Menu — start here | All Staff |
| `/cancel` | ❌ Cancel current action & return | All Staff |
| `/help` | 📖 Command list | All Staff |
| `/version` | 📦 Bot version info | All Staff |
| **Sales** | | |
| `/sales` | 📝 New Sale (skip main menu) | All Staff |
| **Members** | | |
| `/member` | 💳 Member Management menu | All Staff |
| `/newmember` | 🆕 New Member Registration | All Staff |
| `/topup` | 💰 Top Up Member Wallet | All Staff |
| `/check` | 🔍 Check Member Info | All Staff |
| `/ranks` | 📋 View Rank Tier Table | All Staff |
| **Reports** | | |
| `/report` | 📊 Today's Sales Report | All Staff |
| `/freport` | 💹 Financial Report (week + month) | All Staff |
| `/kpi` | 📈 Staff KPI (today) | All Staff |
| `/payroll` | 💰 Monthly Payroll | Admin (PIN) |
| `/setattend` | 📅 Record Leave / Late | All Staff |
| **Stock** | | |
| `/stock` | 📦 Stock Update menu | All Staff |
| `/stockin` | 📥 Stock In (Restock) | All Staff |
| `/stockout` | 📦 Stock Out | All Staff |
| `/inventory` | 🗂 Inventory Status | All Staff |
| `/stocktoday` | 🛒 Items Sold Today | All Staff |
| **Bookings** | | |
| `/bookings` | 📋 Manage Pending Bookings | Admin |
| `/newbooking` | 🆕 Staff Advance Booking | All Staff |
| `/cancelbooking` | ❌ Cancel a Booking | All Staff |
| `/waitlist` | ⏳ Waitlist Management | All Staff |
| **Admin** | | |
| `/admin` | 🔧 Admin Panel (PIN required) | Admin |
| `/broadcast` | 📢 Broadcast message to customers | Admin Only |
| **Console** | | |
| `/console` | 🕹️ Console Live Status | All Staff |
| **Finance** | | |
| `/finance` | 💼 Finance Management (PIN required) | Admin |

---

## Main Menu Overview

When you type `/start`, the Main Menu shows 8 buttons in a 2×4 layout:

```
┌─────────────────────┬─────────────────────┐
│ 📝 Daily Sales      │ 💳 Member Management │
├─────────────────────┼─────────────────────┤
│ 🕹️ Consoles         │ 📊 Today Report     │
├─────────────────────┼─────────────────────┤
│ 📅 Staff Book       │ 🗂️ Inventory View   │
├─────────────────────┼─────────────────────┤
│ 💹 Financial Report │ 🔧 Admin            │
└─────────────────────┴─────────────────────┘
```

Tap any button or type the equivalent `/command` to get started.

### Member Management Sub-Menu

```
┌─────────────────────┬─────────────────────┐
│ 🆕 First Purchase   │ 💰 Top Up           │
├─────────────────────┼─────────────────────┤
│ 🔍 Check Member     │ 📋 View Ranks       │
├─────────────────────┼─────────────────────┤
│ 🔙 Back to Main     │                     │
└─────────────────────┴─────────────────────┘
```

---

## Daily Opening Procedure

1. **Start the day** → `/start` or tap any button
2. **Check console status** → `/console` — verify all consoles are working
3. **Check inventory** → `/inventory` — review stock levels (snacks, drinks, accessories)
4. **Check pending bookings** → `/bookings` (Admin) — approve/reject today's bookings
5. **Review waitlist** → `/waitlist` — reach out to waitlisted customers if slots open
6. **Set staff attendance** → `/setattend` — record who's on shift, late, or on leave
7. **Check today's report** → `/report` — see if previous day was closed properly

---

## Daily Closing Procedure

1. **Final sales check** → `/report` — review all sales recorded today
2. **Check stock** → `/stocktoday` — see items sold today
3. **Review bookings status** → `/bookings` — ensure all bookings are resolved
4. **Ensure all active sessions ended** → `/console` — no consoles still "Active"
5. **Verify financial totals** → `/freport` — check day totals match cash/digital payments
6. **Record any missing sessions** — use Daily Sales for any sessions not yet entered

---

## Common Scenarios

### 🆕 New Customer Walks In (First Visit)

1. `/start` → **Daily Sales** button
2. Staff selects themselves from staff list
3. Select **Guest (0)** or enter new member info
4. For new member: tap **Member Management** → **First Purchase**
5. Enter: Name → Phone → Email → ID Card → Top-up Amount → Gift PIN (if any) → KBZ Pay ref → Referral Code (if any)
6. Confirm registration
7. Back in Daily Sales flow, assign console, set play time, enter food/drink orders
8. Complete sale — voucher is recorded

### 🆕 New Member Registration (Standalone)

- `/newmember` → follow wizard: Name → Phone → Email → ID → Amount → Gift PIN → KBZ Pay → Referral Code
- OR: `/member` → tap **First Purchase**

### 💰 Customer Wants to Top Up

- `/topup` → enter member ID → enter top-up amount → enter KBZ Pay reference → confirm
- OR: `/member` → tap **Top Up**

### 🔍 Check Customer Balance / Info

- `/check` → enter member ID or partial name → view rank, wallet balance, total spend

### 🎮 Customer Finishes Playing

1. `/start` → **Daily Sales**
2. Select **Staff** → select **Member/Console/Mins/Extras**
3. Prompts: food/drink menu → discount/promo → KBZ Pay amount → confirm
4. Session + payment recorded in one flow

### 📞 Customer Calls to Book

1. `/newbooking` → select **console** → enter customer name → date → time → duration → game preference → confirm
2. Admin approves/rejects via `/bookings`
3. When customer arrives → admin taps **Arrived** inline button on booking card

### 📢 Send Promotion to All Customers

> **Admin only**
- `/broadcast PS Vibe Grand Opening Special! 50% off all sessions this weekend! 🎮`
- Message delivered to all customer Telegram contacts who have booked before

### 📦 Restock Items

1. `/stockin`
2. Enter PIN → select item → enter quantity → enter cost → confirm
3. Inventory updated automatically

### 📋 Record Staff Leave / Late

- `/setattend` → select staff → mark Leave/Late → enter hours → confirm deduction
- Supports batch: select one staff, then continue to next

---

## Admin Panel

Accessed via `/admin` (PIN required) or **Admin** button on Main Menu.

```
🔧 Admin Panel
┌─────────────────────┬─────────────────────┐
│ 📦 Stock Update     │ 📅 Attendance       │
├─────────────────────┼─────────────────────┤
│ 💰 Salary Advance   │ 📋 Payroll          │
├─────────────────────┼─────────────────────┤
│ 📈 Staff KPI        │ 🎮 Game Library     │
├─────────────────────┼─────────────────────┤
│ 💹 P&L Report       │ 💵 Cash Flow        │
├─────────────────────┼─────────────────────┤
│ 💳 Liability Report │ 🔙 Back             │
└─────────────────────┴─────────────────────┘
```

### PIN-Protected Actions

Some admin commands prompt for PIN even as shortcuts:
| Command | Purpose |
|---------|---------|
| `/payroll` | View/calculate monthly payroll (PIN) |
| `/kpi` | View today's staff KPI breakdown (PIN) |
| `/setattend` | Record staff attendance/leave/late (PIN) |
| `/finance` | Full Finance Management module (PIN) |

Default PIN is set in `STOCK_ACCESS_PIN` config.

### Salary Advance

1. Admin Panel → **Salary Advance**
2. Select staff → enter amount → select payment method → confirm
3. Deduction tracked for payroll

### Game Library

Accessible via Admin Panel or from Staff Book / Main Menu.

| Action | Description |
|--------|-------------|
| 📄 View Games | List all games in library |
| ➕ Add Game | Add new game (title, platform, genre, status) |
| 🎮 Console Install | Map which games are installed on which console |
| ❌ Delete Game | Remove game from library |
| ✏️ Edit Game | Update game details |
| 💿 Disc Record | Track physical disc count per game |
| 💽 SSD Manage | Map games on external SSDs per console |

---

## Finance Management

Accessed via `/finance` command (PIN required).

```
💼 Finance Management
┌──────────────────────┬──────────────────────┬──────────────────────┐
│ 💰 Capital / Equity  │ 👥 Shareholder Rec.  │ 🔄 Account Transfer │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ 💸 OPEX Record       │ 🏢 Asset Register    │ 🗑️ Asset Disposal   │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ 📅 Prepaid Expenses  │                      │                      │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ 📋 Payables          │ ✅ Settle Payable    │                      │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ 📋 Receivables       │ ✅ Settle Receivable │                      │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ 💳 Advance Payments  │ ✅ Settle Advance    │                      │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ 📊 Account Balances  │ 📈 Financial Reports │                      │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ ⚙️ Setup             │ 🔙 Back              │                      │
└──────────────────────┴──────────────────────┴──────────────────────┘
```

### Finance Actions

| Action | Description |
|--------|-------------|
| **Capital** | Record capital injection into business accounts |
| **Shareholder** | Record shareholder names, roles, capital contributions, ownership % |
| **Account Transfer** | Transfer money between accounts |
| **OPEX** | Record operating expenses (category, description, amount, account, payment method) |
| **Asset Register** | Record new assets (name, category, date, cost, qty, useful life, salvage value, account) |
| **Asset Disposal** | Dispose of assets (select asset, date, qty, proceeds) |
| **Prepaid Expenses** | Record prepaid expenses (description, category, amount, account, start/end dates) |
| **Payables** | Record bills to pay (vendor, description, amount, due date, account) |
| **Settle Payable** | Mark a payable as paid |
| **Receivables** | Record money owed by customers (customer, description, amount, due date, account) |
| **Settle Receivable** | Mark a receivable as received |
| **Advance Payment** | Record advance payments (party, description, amount, account, due date, notes) |
| **Settle Advance** | Settle an advance payment |
| **Account Balances** | View all account balances |
| **Financial Reports** | View P&L, Cash Flow, Liability reports |
| **Setup** | Configure finance accounts |

---

## Tips & Troubleshooting

### General Tips

- **Always use the keyboard buttons** — they guide you through the flow step-by-step
- **Cancel anytime** — type `/cancel` to abort and return to Main Menu
- **Search for members** — on member selection screens, type part of the ID or name to filter
- **Guest mode** — select "0 (Guest)" for non-member walk-in customers
- **Voucher numbers** are auto-assigned and tracked in Google Sheets

### Common Issues

| Issue | Solution |
|-------|----------|
| Bot not responding | Wait a few seconds; the bot refreshes caches every 5 minutes |
| "Access Denied" | Your Telegram ID is not in the staff whitelist — ask admin to add it |
| PIN not working | Check with admin; PIN is configured in server settings |
| Member not found | Double-check spelling; search by partial ID works |
| Console showing wrong status | Check `/console` — if stuck, admin can manually update via Sheets |
| Booking not appearing | Customer may not have completed the booking — check waitlist |

### Important Notes

- **Grand Opening:** June 6, 2026 — expect high volume; use shortcuts (`/newmember`, `/topup`, `/sales`) for speed
- **All data** is stored in Google Sheets and a PostgreSQL database
- **Staff KPI** is calculated daily — check `/kpi` to see performance
- **Payroll** runs monthly — verify attendance records are complete before payroll date
- **Wallet top-ups** give bonus minutes based on member rank (Warrior/Master/Immortal)
- **Referral codes** can be assigned to members with a Member Card

---

> **Need help?** Contact the development team or check the bot's `/help` command.
> Last updated: June 2, 2026
