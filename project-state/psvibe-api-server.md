# PS VIBE API Server — Project State

**Repo:** /root/psvibe_api_server/ (GitHub: flash00787/PSVIBE-API-Server)
**Service:** psvibe-api.service (FastAPI, port 8000)
**Staging:** https://ps-vibe.com/api/ (via Cloudflare + Caddy)

## Services
- `psvibe-api.service` — Main API server (uvicorn)
- `sync_service.py` — GSheet→MySQL sync (cron every 5 min via run_sync.sh)

## Latest Status
- Git HEAD: a86d9c0 (in sync with remote)
- All pushes unblocked (kora_drive_sa.json removed from history)
- Rate config cache added (195baa4, 60s TTL)
- MySQL: all 4 tables synced (games_library, console_status, console_games, staff_records)
- Member wallet migration: member_wallets + topup_log tables active

## Alignment with Bot
The API server repo is the BACKEND for the bot. Changes to API server often fix bugs that appear in the bot. Always check BOTH repos.

## Recent Fixes (2026-06-02)
- 🔧 `patch_routes.py` — Missing comma after `"phone"` caused SyntaxError → API crash loop (restart counter 65)
- All 3 services now active (psvibe-api, psvibe_customer_bot, psvibe-sale-bot)
