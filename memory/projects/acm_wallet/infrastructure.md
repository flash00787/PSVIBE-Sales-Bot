# ACM Wallet — Infrastructure

## Project Overview
- **Type:** Python Telegram Bot
- **Owner:** Ko Aung Chan Myint
- **Slug:** `acm_wallet`
- **Repository:** `flash00787/ACM-Personal-Wallet`

## Code Paths
| Path | Purpose |
|------|---------|
| `/root/ACM-Personal-Wallet/` | Deployment root |
| `/root/ACM-Personal-Wallet/bot/` | Primary runtime directory |
| `/root/ACM-Personal-Wallet/bot/main.py` | Entry point (246KB — full bot logic) |
| `/root/ACM-Personal-Wallet/bot/keep_alive.py` | Flask daemon for UptimeRobot (port 5000) |
| `/root/ACM-Personal-Wallet/bot/bot/` | Sub-module (mostly log files) |
| `/root/ACM-Personal-Wallet/lib/` | Shared libraries (api-spec, db schema, zod) |

## Services
| Service | Status | Type |
|---------|--------|------|
| `acm-personal-wallet.service` | active | systemd |

### Service Details
```
WorkingDirectory: /root/ACM-Personal-Wallet/bot
ExecStart: psvibe-pidlock.sh acm-wallet → venv/bin/python bot/main.py
User: root
Restart: always, 5s
```

## Database
- **None locally** — uses **Google Sheets** via `gspread` library
- Reads/writes `Transaction_Log` worksheet
- Columns: Date, Type, Category, AccountFrom, AccountTo, Amount, Project, Scope

## Dependencies
```python
flask>=3.1.3
google-auth>=2.50.0
gspread>=6.2.1
python-telegram-bot[job-queue]>=22.7
```

## Logging
- Rotating file: `bot/bot_status.log` (5MB × 3 backups)
- Journal: `journalctl -u acm-personal-wallet`

## Important Notes
- Uses `PicklePersistence` for ConversationHandler state
- Uses `psvibe-pidlock.sh` (shared lock script) to prevent duplicate instances
- `drop_pending_updates=True` on start
- Self-healing: main() wrapped in while-True/try-except, auto-restart 5s
- Codebase is identical to YYO Wallet — separate instance with different bot token

## Health Checks
```bash
systemctl is-active acm-personal-wallet
journalctl -u acm-personal-wallet -n 20
```

## Related Projects
- **YYO Wallet:** Same codebase, separate instance, different bot token
- **PS VIBE:** Shares `psvibe-pidlock.sh`
