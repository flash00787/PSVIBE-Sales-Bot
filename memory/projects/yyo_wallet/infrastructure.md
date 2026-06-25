# YYO Wallet — Infrastructure

## Project Overview
- **Type:** Python Telegram Bot
- **Owner:** Ko Aung Chan Myint
- **Slug:** `yyo_wallet`
- **Repository:** `flash00787/YYO-Personal-Wallet`

## Code Paths
| Path | Purpose |
|------|---------|
| `/opt/yyo-personal-wallet/` | Active deployment root |
| `/opt/yyo-personal-wallet/bot/` | Primary runtime directory |
| `/opt/yyo-personal-wallet/bot/main.py` | Entry point (246KB — full bot logic) |
| `/opt/yyo-personal-wallet/bot/keep_alive.py` | Flask daemon for UptimeRobot (port 5000) |
| `/opt/yyo-personal-wallet/bot/bot/` | Sub-module (mostly log files) |
| `/opt/yyo-personal-wallet/lib/` | Shared libraries (api-spec, db schema, zod) |
| `/root/YYO-Personal-Wallet/` | Git/backup copy |

## Services
| Service | Status | Type |
|---------|--------|------|
| `yyo-personal-wallet.service` | active | systemd |

### Service Details
```
WorkingDirectory: /opt/yyo-personal-wallet/bot
ExecStart: psvibe-pidlock.sh yyo-wallet → venv/bin/python3 bot/main.py
EnvFile: /opt/yyo-personal-wallet/bot/.env
User: root
Restart: always, 10s
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
- Journal: `journalctl -u yyo-personal-wallet`

## Important Notes
- Uses `PicklePersistence` for ConversationHandler state
- Uses `psvibe-pidlock.sh` (shared lock script) to prevent duplicate instances
- `drop_pending_updates=True` on start
- Self-healing: main() wrapped in while-True/try-except, auto-restart 5s

## Health Checks
```bash
systemctl is-active yyo-personal-wallet
journalctl -u yyo-personal-wallet -n 20
```

## Related Projects
- **ACM Wallet:** Same codebase, separate instance, different bot token
- **PS VIBE:** Shares `psvibe-pidlock.sh`
