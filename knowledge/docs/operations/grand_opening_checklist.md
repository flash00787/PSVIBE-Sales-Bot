# GRAND OPENING CHECKLIST
> Auto-imported from `/root/psvibe-sales-bot/GRAND_OPENING_CHECKLIST.md`

# 🎮 PS VIBE - PS5 Gaming Lounge Grand Opening Checklist
**Date:** Saturday, June 6, 2026 | **Hours:** 9:00 AM - 9:00 PM
**Address:** No. 17, Mau Pin Street, Sanchaung, Yangon
**Tagline:** Play The Game. Share The VIBE!

## ✅ System Readiness (Already Done)
- [x] All 3 services running (sale-bot, customer-bot, API)
- [x] MySQL backup configured (daily 4AM cron)
- [x] Pending bookings display bug fixed
- [x] Receipt template (multi-type: new_member, topup, gaming)
- [x] Dynamic payment methods (Cash, KPay, Wave, CB Pay)
- [x] My Booking / customer notifications
- [x] Booking ↔ Console Status Link
- [x] System stability: concurrent limits reduced, disk 500mb
- [x] API Server committed + pushed (e6ce993)

## 🔴 CRITICAL — Must Do Before June 6
- [ ] Load test — simulate 10+ concurrent customer sessions
- [ ] Disaster recovery plan (what if API crashes?)
- [ ] MySQL emergency restore procedure documented
- [ ] Verify opening hours (9AM-9PM) in constants.py

## 📋 Operations
- [ ] Opening day promo/pricing in Ko VIBE AI
- [ ] Staff Telegram accounts added to bot allowlist
- [ ] Test full customer flow: walk-in → create member → play → checkout
- [ ] Test booking flow: call → book → confirm → play → done
- [ ] Verify receipt prints correctly
- [ ] Staff training on bot commands

## 📢 Communication
- [ ] Opening day announcement ready
- [ ] Ko VIBE bot greeting updated with opening info
- [ ] Menu boards/signage verified

## ⏱️ Suggested Schedule
- **Jun 2 (Today):** Load test + Staff runbook
- **Jun 3:** Disaster recovery plan + MySQL restore doc
- **Jun 4:** Final smoke test + Staff training
- **Jun 5:** Dress rehearsal + Team briefing

---
*Imported on 2026-06-11*