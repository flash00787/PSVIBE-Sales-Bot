# 📘 PS VIBE Gaming Lounge — Staff Runbook
**Bot:** @psvibe_staff_bot
**Version:** Latest
**Last Updated:** June 2, 2026

---

## 📋 Table of Contents
1. [Daily Opening Procedure](#daily-opening-procedure)
2. [All Commands Reference](#all-commands-reference)
3. [Common Scenarios](#common-scenarios)
4. [Troubleshooting](#troubleshooting)

---

## 1. Daily Opening Procedure

### 🕐 Morning Start (Before 9:00 AM)
1. /start — Open bot main menu
2. Verify all services are running:
   `systemctl is-active psvibe-sale-bot psvibe_customer_bot psvibe-api`
3. /report — Check yesterday's ending report
4. /stocktoday — Review what stock needs replenishment
5. /inventory — Check current stock levels
6. Verify console statuses are all "Available"
7. Check /booking hub for today's pre-bookings

### 🕐 Closing Procedure (After 9:00 PM)
1. Process any remaining member checkouts via /sales
2. /report — Generate end-of-day report
3. /stockin — Log any restock for tomorrow
4. /payroll — Verify today's staff attendance is recorded
5. Log out of bot

---

## 2. All Commands Reference

### 🏠 Navigation
| Command | Description |
|---------|-------------|
| /start | Main Staff Menu |
| /menu | Main Staff Menu (alternative) |
| /cancel | Cancel current action / go back |
| /help | Show all available commands |

### 🎮 Sales
| Command | Description |
|---------|-------------|
| /sales | New Sale Entry — start a new transaction |
| /member | Member Management menu |
| /newmember | Register a new member |
| /topup | Top Up member wallet balance |
| /check | Look up member info |
| /ranks | View Rank / Tier table |

### 💰 Finance
| Command | Description |
|---------|-------------|
| /finance | Finance menu (PIN-protected) |
| /report | Today's full report |
| /financial | Financial reports (P&L, Cash Flow, Liabilities) |

### 🔧 Admin (PIN-Protected)
| Command | Description |
|---------|-------------|
| /admin | Admin Panel (PIN required) — Stock, Attendance, Payroll, KPI |
| /setattend | Record leave / late |
| /payroll | Monthly payroll view |
| /kpi | Today's staff KPI |

### 📦 Stock
| Command | Description |
|---------|-------------|
| /stock | Stock Update menu |
| /stockin | Stock In — record restock |
| /stockout | Stock Out — record removal/write-off |
| /inventory | View full inventory status |
| /stocktoday | Items sold today |

### 🎮 Gaming & Consoles
| Command | Description |
|---------|-------------|
| /consoles | Consoles menu — View console status |
| /booking | Staff Booking Hub |
| /game | Game library menu |
| /waitlist | Waitlist management |

### 📢 Communication
| Command | Description |
|---------|-------------|
| /broadcast | Send broadcast message to all customers (Admin only) |
| /discount | Discount management |

---

## 3. Common Scenarios

### Scenario A: Walk-In New Member → Play → Checkout
1. /newmember → Enter customer name & phone → Set initial topup
2. /sales → Select the new member → Add gaming session items
3. Assign console via /consoles → Mark as "In Use"
4. When session ends: /sales → Process payment (Cash/KPay/Wave/CB Pay)
5. Print receipt → Hand to customer
6. Mark console as "Available" via /consoles

### Scenario B: Existing Member Topup
1. /topup → Search member by name/phone
2. Select amount and payment method
3. Confirm → System adds to wallet balance
4. Receipt prints automatically

### Scenario C: Phone Booking → Confirm → Play
1. Customer calls → /booking → New Booking
2. Enter customer name, phone, preferred console, time slot
3. /booking → Confirmed Bookings to see today's bookings
4. When customer arrives: Check in via /consoles → Mark console "In Use"
5. /sales → Process gaming session payment

### Scenario D: Stock Restock
1. /stockin → Select item category
2. Enter quantity received → Confirm
3. Inventory auto-updates → /inventory to verify

### Scenario E: End of Day Cashup
1. /report → Review today's total sales
2. /financial → Check P&L and Cash Flow
3. Cross-check with physical cash drawer
4. Log any discrepancies

---

## 4. Troubleshooting

### Bot Not Responding
- Check service status: `systemctl is-active psvibe-sale-bot`
- Restart: `systemctl restart psvibe-sale-bot`
- Check logs: `journalctl -u psvibe-sale-bot --no-pager -n 50`

### API Server Down
- Check: `systemctl is-active psvibe-api`
- Restart: `systemctl restart psvibe-api`
- If MySQL issue: `systemctl restart mysql`

### Booking Not Showing
- Verify console is marked "Available" first
- Check /booking → Confirmed Bookings
- If data inconsistency: Restart customer bot

### Receipt Not Printing
- Check printer connection
- Verify receipt template is loading
- Try printing from a different terminal

### Access Denied
- Your Telegram ID must be in the staff allowlist
- Contact admin to add: /admin → Staff Management

### Stuck in Conversation
- If stuck in a conversation, type /start to reset
- Or type /cancel

---

> **Emergency Contact:** System Admin — Telegram DM
> **Server Access:** SSH root@5.223.81.16 (Key-based auth)

