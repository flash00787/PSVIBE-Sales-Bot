# TOOLS.md — Local Notes

## Project Onboarding (NEW — Multi-Project)
```bash
# Standard convention (auto-creates /opt/kora-projects/<slug>/code/ + config/)
python3 /root/coordination/onboard_project.py mybot "My Bot" /opt/kora-projects/mybot/code \
    --type telegram-bot --language python --services "mybot-bot"

# Interactive mode
python3 /root/coordination/onboard_project.py --interactive

# Dry-run (preview without creating)
python3 /root/coordination/onboard_project.py --dry-run mybot "My Bot" /opt/kora-projects/mybot/code

# Without convention (custom path)
python3 /root/coordination/onboard_project.py mybot "My Bot" /root/my-custom-bot --no-convention
```
> **Convention:** New projects → `/opt/kora-projects/<slug>/code/`  
> **Full docs:** See `memory/CONVENTIONS.md`

## SSH
- **bot-server-01:** `5.223.81.16` (root@) — Key: `.ssh/id_boss`
- **Connection:** Node.js `ssh2` package

## API Keys
- **Grok (xAI):** `xai-...` — Researcher (Grok 4.3)
- **OpenRouter:** `sk-or-...` — Claude Sonnet 4 (last resort fixer)

## Bots & Services
| Bot | Location | Service |
|-----|----------|---------|
| PS VIBE Sale Bot | `/root/psvibe-sales-bot/` | `psvibe-sale-bot` |
| PS VIBE Customer Bot | `/root/psvibe-sales-bot/` | `psvibe_customer_bot` |
| PS VIBE API | `/root/psvibe_api_server/` | `psvibe-api` |
| Construction Bot | `/opt/construction-bot/` (Docker) | `@three_brothers_accounting_bot` |
| YYO Wallet Bot | `/opt/yyo-personal-wallet/` | `yyo-personal-wallet` |
| PS VIBE Analytics | — | `psvibe-analytics.service` |
| Staff Attendance | — | `psvibe-attendance.service` |
| Discord Bot | — | `psvibe-discord-bot.service` |
| Kora Host API | — | `kora-host-api.service` |
| Kora Voice | — | `kora-voice.service` |
| ACM Wallet Bot | `/opt/acm-personal-wallet/` | `acm-personal-wallet.service` |

## Research Agent
```bash
# Deep research on any topic (saves to memory/research/)
node /root/.openclaw/workspace/research_agent.js "your research query" [--timeout 120]

# Example
node /root/.openclaw/workspace/research_agent.js "Latest PS5 game releases June 2026"
```

## Google Drive Integration
```bash
# Upload file to Drive
python3 /root/.openclaw/workspace/drive_tool.py upload <local_path> [--folder-id <id>]

# List files
python3 /root/.openclaw/workspace/drive_tool.py list [--folder-id <id>]

# Create folder
python3 /root/.openclaw/workspace/drive_tool.py mkdir <name> [--parent-id <id>]

# Share / delete / search
python3 /root/.openclaw/workspace/drive_tool.py share <file_id>
python3 /root/.openclaw/workspace/drive_tool.py delete <file_id>
python3 /root/.openclaw/workspace/drive_tool.py search <query>
```

## Essential Commands
```bash
# Multi-Project Coordination (NEW — Phase 5)
python3 /root/coordination/kora_status.py              # All projects health dashboard
python3 /root/coordination/kora_status.py --json       # JSON output for automation
python3 /root/coordination/kora_status.py --project psvibe  # Single project detail
python3 /root/coordination/onboard_project.py --help   # One-command new project setup
python3 /root/coordination/backup_manager.py backup    # Backup all projects
python3 /root/coordination/backup_manager.py list      # List all backups
python3 /root/coordination/backup_manager.py cleanup --days 30  # Cleanup old backups
python3 /root/coordination/project_utils.py detect "<message>"  # Auto-detect project from message
python3 /root/coordination/project_utils.py list       # List all projects
python3 /root/coordination/project_utils.py set-context <slug>  # Set current project context

# Core dev
python3 /root/coordination/quality_gate.py --quick
python3 /root/coordination/tool_orchestrator.py 2>&1 | tail -20

# Workflow
python3 /root/coordination/workflow_engine.py --run quality|full-audit|safe-fix|auto-deploy

# Fix Protocol (MANDATORY before ANY code fix)
python3 /root/coordination/fix_protocol.py --start <file>
python3 /root/coordination/fix_protocol.py --complete

# Documentation
python3 /root/coordination/auto_doc_updater.py --summary "Fixed X: ..."

# Other
python3 /root/coordination/check_alerts.py
sudo /root/psvibe_api_server/run_sync.sh
python3 /root/coordination/dashboard.py --port 9090
```
> **Full detail:** See `memory/tools-commands.md` for all commands + coordination tool tables
> **Contacts:** See `memory/contacts.md`
> **Infrastructure:** See `memory/infrastructure.md`
