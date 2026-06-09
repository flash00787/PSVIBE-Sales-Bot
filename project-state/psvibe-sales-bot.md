# PS VIBE Sales Bot — Project State

## Current Status (2026-06-02 10:50 UTC)

### Services
- ✅ `psvibe-api.service` — Active (FastAPI, :8000, MySQL)
- ✅ `psvibe-sale-bot.service` — Active
- ✅ `psvibe_customer_bot.service` — Active

### Repositories
1. **Bot:** `/root/psvibe-sales-bot/` → GitHub `flash00787/PSVIBE-Sales-Bot`
   - HEAD: `3e64f82` (topup fix) — pushed ✅
2. **API Server:** `/root/psvibe_api_server/` → GitHub `flash00787/PSVIBE-API-Server`
   - HEAD: `064dfdf` (games MySQL restore) — 2 commits unpushed ❌ (gh push protection)
   - Blocked by: kora_drive_sa.json in c4ea16a

### Database
- MySQL Docker container `psvibe-mysql` (127.0.0.1:3306)
- DB: `psvibe_api`, User: `psvibe_user`
- Tables: member_wallets, games_library, console_status, staff_records — all synced (51 rows)
- Sync: cron every 5 min via `/root/psvibe_api_server/run_sync.sh`

### Recent Fixes (2026-05-31)
| Fix | Repo | Commit | Status |
|-----|------|--------|--------|
| ✏️ Booking auto-confirm + PS5/Pro dupe | Bot | `2be094d` | ✅ |
| 📊 Rate display (Settings tab) | Bot | `2be094d` | ✅ |
| 🆕 Member create (wrong ID + mins) | API | `064dfdf` | ✅ |
| 💰 Topup not working | Bot + API | `3e64f82` + `ef9d733` | ✅ |
| 🎮 Game list (console codes fix) | API | `064dfdf` + sync | ✅ |
| 🏎️ Sales speed (timeout reduce) | Bot + API | `ecca9f2` + `76f203f` | ✅ |
| 🔄 MySQL sync fix | API | run_sync.sh → venv python | ✅ |

### Recent Fixes (2026-06-02)
| Fix | Repo | Status |
|-----|------|--------|
| 🤖 Ko VIBE system prompt update (new tone + shop info) | Bot | ✅ |
| ⏰ FAQ hours 10-10 → 9-9 | Bot (faq.py) | ✅ |
| 🔧 MarkdownV2 escape for faq_reply (Technical Error fix) | Bot (ai.py, handlers.py) | ✅ |
| 🔧 API crash fix — patch_routes.py missing comma | API | ✅ |
| 📍 Added shop info to Ko VIBE prompt (address, hours, opening date June 6, pre-booking=testing) | Bot (prompts.py) | ✅ |

### Known Issues
1. **Git push blocked** — API Server needs filter-branch to remove SA key from c4ea16a
2. **Booking display in Sale Bot** — Still not working (pending bookings not showing details)
3. **Game genre empty** — Sheet Column U lacks `solo_multi|genre` format data
4. **Tests** — 33 tests at `/root/psvibe-sales-bot/tests/`

### Known Issues
1. **Git push blocked** — API Server needs filter-branch to remove SA key from c4ea16a
2. **Game genre empty** — Sheet Column U lacks `solo_multi|genre` format data
3. **Tests** — 33 tests at `/root/psvibe-sales-bot/tests/`

### Dashboard
- URL: https://ps-vibe.com/dashboard/
- Caddy reverse proxy :80 → :9090
- Cloudflare tunnel (cloudflared-tunnel.service)
