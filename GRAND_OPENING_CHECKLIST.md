# 🎮 PS VIBE — PS5 Gaming Lounge Grand Opening Checklist
**Date:** Saturday, June 6, 2026 | **Hours:** 9:00 AM — 9:00 PM
**Tagline:** *Play The Game. Share The VIBE!*

---

## Status Overview

| Icon | Meaning |
|------|---------|
| ✅ | Done |
| 🟡 | In Progress |
| ❌ | Not Started |
| 🔲 | Not Applicable / Deferred |

---

## 📌 Section 1: System Readiness — Already Complete ✅

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | All 3 services running (psvibe-sale-bot, psvibe_customer_bot, psvibe-api) | ✅ | Confirmed healthy via systemctl |
| 2 | MySQL backup configured (daily 4 AM) | ✅ | Docker container `psvibe-mysql`, auto-backup cron |
| 3 | Pending bookings fix applied | ✅ | SHA `6e3c556` in project-state |
| 4 | Receipt template (multi-type) | ✅ | PDF/HTML via `report_generator.py` |
| 5 | Dynamic payment methods | ✅ | Cash / bank transfer / wallet balance |
| 6 | My Booking / customer notifications | ✅ | Telegram push; friendly Burmese empty-state (SHA `6e3c556`) |
| 7 | Booking ↔ Console Status Link | ✅ | Auto Scheduled/Done; status icons 🟢🔴⚫🟡 (SHA `941d0a5`) |
| 8 | Session lock timeout fix (60s → 300s) | ✅ | `acquireTimeoutMs` applied in config |
| 9 | Watchdog service (psvibe-watchdog) running | ✅ | Auto-heals on crash |
| 10 | Git backup (GitHub: `flash00787/PSVIBE-Sales-Bot`) | ✅ | Both bot & API server repos |

---

## ⚠️ Section 2: CRITICAL — Must Do Before June 6

### 2.1 Staff Bot Commands Runbook
- [ ] ❌ Document all staff-facing bot commands in a one-page runbook:
  - `/start` — bot welcome + role routing
  - `/create_member` — walk-in member registration
  - `/topup` — balance top-up (cash / bank transfer)
  - `/booking` — create / view / cancel bookings
  - `/checkout` — end session + generate receipt
  - `/status` or `/console_status` — console availability
  - `/report` — daily / shift sales report
- [ ] ❌ Print runbook & keep beside each terminal
- [ ] ❌ Share PDF version in staff Telegram group

### 2.2 Load Testing
- [ ] ❌ Simulate 10+ concurrent customer sessions hitting the API
- [ ] ❌ Test peak: 5 walk-ins + 3 bookings + 2 checkouts simultaneously
- [ ] ❌ Verify API response < 2s under load
- [ ] ❌ Check MySQL connection pool doesn't exhaust
- [ ] ❌ Ensure watchdog triggers if any service stalls
- [ ] ❌ Document max concurrent session capacity

### 2.3 Disaster Recovery Plan
- [ ] ❌ Write step-by-step recovery if API crashes:
  1. SSH into VPS (`5.223.81.16`)
  2. `systemctl status psvibe-api`
  3. `systemctl restart psvibe-api`
  4. `journalctl -u psvibe-api --tail -50`
  5. If watchdog unresponsive: `systemctl restart psvibe-watchdog`
- [ ] ❌ Document full server reboot procedure
- [ ] ❌ Create "Emergency Mode" SOP — cash-only walk-ins if systems down

### 2.4 MySQL Emergency Restore Procedure
- [ ] ❌ Document MySQL restore:
  1. `docker exec -it psvibe-mysql bash`
  2. `ls -lt /backup/mysql/`
  3. `mysql -u root -p psvibe_db < /backup/mysql/psvibe_db_YYYYMMDD.sql`
- [ ] ❌ Verify a backup file exists & is restorable
- [ ] ❌ Confirm backup cron is running (check timestamps)
- [ ] ❌ Test a dry-run restore on a temp database

### 2.5 Verify Opening Hours in Code
- [ ] ❌ Check `constants.py` confirms **9 AM — 9 PM**
- [ ] ❌ Verify closing logic: no new sessions after 9 PM
- [ ] ❌ Confirm automated "closed" messages trigger correctly
- [ ] ❌ Check all time-zone logic uses Myanmar Time (MMT)

### 2.6 Network & Hardware Check
- [ ] ❌ Test staff Wi-Fi credentials are correct
- [ ] ❌ Verify all PS5 consoles on LAN & reachable
- [ ] ❌ Check LAN cable / switch status for each console station
- [ ] ❌ Confirm monitor/TV input sources & audio settings
- [ ] ❌ Test controller pairing for each console
- [ ] ❌ Have spare controllers & charging cables ready

---

## 🛠️ Section 3: Operations

### 3.1 Opening Day Promo & Pricing
- [ ] ❌ Define promo pricing in Ko VIBE AI / bot config:
  - [ ] ❌ First-hour free/discounted?
  - [ ] ❌ Bundle deals (2h + drink)?
  - [ ] ❌ Membership fee waived for first 10/20 customers?
- [ ] ❌ Set promo start & end times in system
- [ ] ❌ Test promo applies correctly at checkout

### 3.2 Staff Access
- [ ] ❌ Collect all staff Telegram usernames/IDs
- [ ] ❌ Add staff accounts to bot allowlist
- [ ] ❌ Assign correct roles (admin, staff, etc.)
- [ ] ❌ Test each staff account can log in & use commands

### 3.3 Full Customer Walk-in Flow
- [ ] ❌ Walk in → `/create_member` → enter name/phone → member created
- [ ] ❌ `/topup` → enter amount → payment collected → balance updated
- [ ] ❌ Start game → console 🟢→🔴 → timer starts
- [ ] ❌ Finish → `/checkout` → session ends → receipt prints
- [ ] ❌ Verify receipt: date, time, duration, rate, total, payment, remaining balance

### 3.4 Full Booking Flow
- [ ] ❌ Call → `/booking` → select date/time → pick console → confirm
- [ ] ❌ Booking confirmation sent via Telegram notification
- [ ] ❌ Console status → 🟡 RESERVED
- [ ] ❌ Customer arrives → start session → 🟡→🔴 (in use)
- [ ] ❌ Session ends → 🟢 (free)
- [ ] ❌ **Edge cases:**
  - [ ] ❌ Overlapping booking rejected
  - [ ] ❌ Cancel → console released
  - [ ] ❌ No-show → auto-release after 15 min grace

### 3.5 Receipt Verification
- [ ] ❌ Cash payment receipt
- [ ] ❌ Bank transfer receipt
- [ ] ❌ Wallet balance deduction receipt
- [ ] ❌ Mixed payment (cash + wallet) receipt
- [ ] ❌ Receipt looks professional (logo, branding, totals)
- [ ] ❌ Test reprint (if available)

### 3.6 Pre-Open Dress Rehearsal
- [ ] ❌ Full shift timeline rehearsal (9 AM — 9 PM)
- [ ] ❌ Opening process: consoles on → bots boot → verify connectivity (< 10 min)
- [ ] ❌ Closing process: end sessions → settle tabs → power-off → backup trigger

---

## 📣 Section 4: Communication

### 4.1 Opening Day Announcement
- [ ] ❌ Draft announcement (Burmese / English):
  - Opening date & time
  - Location & directions
  - Promo offers
  - Booking contact info
  - Hashtags: #PSVIBE #PS5Gaming #GrandOpening
- [ ] ❌ Schedule on Facebook page
- [ ] ❌ Schedule on Telegram channel
- [ ] ❌ Schedule on Instagram (if applicable)
- [ ] ❌ Prepare Google Maps / Waze link
- [ ] ❌ Prepare broadcast to existing prospect list

### 4.2 Ko VIBE AI Bot Greeting
- [ ] ❌ Update welcome message with grand opening info
- [ ] ❌ Add quick-reply buttons: "📍 Location", "🎮 Pricing", "📞 Book Now", "🎉 Promo"
- [ ] ❌ Test greeting flow end-to-end
- [ ] ❌ Ensure opening hours (9 AM — 9 PM) are prominently shown

### 4.3 Staff Briefing
- [ ] ❌ Schedule staff meeting (at least 1 day before)
- [ ] ❌ Walk through runbook together
- [ ] ❌ Assign opening-day roles:
  - Reception / member registration
  - Console management
  - Food & beverage (if applicable)
  - Cashier / checkout
  - Tech support (on-call)
- [ ] ❌ Share emergency contact numbers

---

## ✅ Section 5: Opening Day Timeline

| Time | Item | Done? |
|------|------|-------|
| **8:00 AM** | Power on all PS5 consoles | ❌ |
| **8:10 AM** | Check all consoles boot & network connect | ❌ |
| **8:20 AM** | Verify all 3 services: `systemctl status` | ❌ |
| **8:25 AM** | API health: `curl localhost:8000/health` | ❌ |
| **8:30 AM** | Test Wi-Fi for customer devices | ❌ |
| **8:35 AM** | Verify receipt printer / PDF generation | ❌ |
| **8:40 AM** | Stock snacks/drinks (if applicable) | ❌ |
| **8:45 AM** | Clean consoles, controllers, seating | ❌ |
| **8:50 AM** | Staff stand-up + role assignment + runbook review | ❌ |
| **8:55 AM** | **Open doors!** 🚀 | ❌ |
| **9:00 AM** | 🎉 **GRAND OPENING — GO!** 🎉 | ❌ |
| **12:00 PM** | Mid-day check: bot uptime, console statuses | ❌ |
| **6:00 PM** | Evening rush prep: top up snacks, check balances | ❌ |
| **8:45 PM** | Closing prep: no new sessions started | ❌ |
| **9:00 PM** | Finalize sessions, generate daily report, close | ❌ |

---

## 🔧 Quick Reference

### Service Commands
```bash
# Check status
systemctl status psvibe-sale-bot
systemctl status psvibe_customer_bot
systemctl status psvibe-api
systemctl status psvibe-watchdog

# Restart (if needed)
systemctl restart psvibe-sale-bot
systemctl restart psvibe_customer_bot
systemctl restart psvibe-api

# View logs
journalctl -u psvibe-sale-bot --tail -50
journalctl -u psvibe_customer_bot --tail -50
journalctl -u psvibe-api --tail -50

# MySQL
docker exec -it psvibe-mysql bash
mysql -u root -p psvibe_db               # (password from .env)
```

### VPS Info
- **IP:** `5.223.81.16`
- **SSH:** `root@5.223.81.16` (key-based auth)
- **Bot path:** `/root/psvibe-sales-bot/`
- **API path:** `/root/psvibe_api_server/`

### Console Status Icons
| Icon | Meaning |
|------|---------|
| 🟢 | FREE |
| 🔴 | IN USE |
| ⚫ | OFF |
| 🟡 | RESERVED |

---

## 📊 Progress Tracker

```
System Readiness (Section 1):     ✅ 10/10  ████████████████████████████████████████████░░░░░░░░  80%
Critical Pre-Opening (Section 2): ❌ 0/17   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%
Operations (Section 3):           ❌ 0/20   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%
Communication (Section 4):        ❌ 0/10   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%
Opening Day (Section 5):          ❌ 0/15   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%
```

**Overall:** ✅ 10 done | ❌ ~62 to go

*Last updated: 2026-06-02 14:51 UTC | Updated by PS VIBE automation*
