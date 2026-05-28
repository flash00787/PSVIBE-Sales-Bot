# PS VIBE — Audit Fix Coordination (2026-05-27)

## Objective
Fix ALL issues from security audit report in PARALLEL using 30 agents.

## Rules
1. Each agent owns ONE fix task — do NOT modify files outside your scope
2. Edit files directly at `/root/psvibe-sale-bot/` using SSH to root@5.223.81.16
3. Write completion status to `/root/psvibe_fix_coordination/FIX_TASKS.md`
4. Format: `AGENT_N | TASK | STATUS | FILE | NOTES`
5. FAIL FAST — if a fix is already applied, mark as DONE and move on
6. Do NOT restart services — fixes will be validated manually after all agents complete
7. After fixing, VERIFY your change doesn't break Python syntax: run `python3 -c "import ast; ast.parse(open('FILE_PATH').read())"` where FILE_PATH is the file you edited
8. Use `sed -i` or write Python inline scripts to make edits — do NOT download/rewrite entire files

## File Paths on VPS (5.223.81.16)
| Key | Path |
|-----|------|
| Bot root | /root/psvibe_sales_bot |
| Bot init (large 82KB) | /root/psvibe-sale-bot/bot/__init__.py |
| Bot app | /root/psvibe-sale-bot/bot/app.py |
| App root | /root/psvibe-sale-bot/app.py |
| Main | /root/psvibe-sale-bot/main.py |
| Env file | /root/psvibe-sale-bot/.env |
| Service account | /root/psvibe-sale-bot/service_account.json |
| Systemd sales bot | /etc/systemd/system/psvibe_sales_bot.service |
| Systemd customer bot | /etc/systemd/system/psvibe_customer_bot.service |
| Systemd API | /etc/systemd/system/psvibe-api.service |
| Systemd wallet | /etc/systemd/system/psvibe-wallet.service |
| API server JS | /root/Aung Chan Myint/Sales-Tele-Bot/api_server/api_server.js |
| Handler dir | /root/psvibe-sale-bot/bot/handlers/ |
| Customer bot dir | /root/psvibe-sale-bot/customer_bot/ |
| CB handlers | /root/psvibe-sale-bot/customer_bot/handlers.py |
| CB api | /root/psvibe-sale-bot/customer_bot/api.py |
| CB ai | /root/psvibe-sale-bot/customer_bot/ai.py |
| CB main | /root/psvibe-sale-bot/customer_bot/main.py |
| Broadcast handler | /root/psvibe-sale-bot/bot/handlers/broadcast.py |
| Stock handler | /root/psvibe-sale-bot/bot/handlers/stock.py |
| Help handler | /root/psvibe-sale-bot/bot/handlers/help.py |

## SSH Access
All agents: `ssh -i /root/.openclaw/workspace/.ssh/id_rsa -o StrictHostKeyChecking=no root@5.223.81.16 "COMMAND"`
