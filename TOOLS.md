# TOOLS.md — Local Notes

## SSH
- **bot-server-01:** `5.223.81.16` (root@) — Key: `.ssh/id_rsa`
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

## Essential Commands
```bash
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
