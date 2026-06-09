# fix_start_script.md — Fix start_bots_v3.sh (IN-2)

**Date:** 2026-05-28 12:40 UTC
**VPS:** 5.223.81.16

## What Changed

Updated `/root/start_bots_v3.sh` from v3 to v3.1:

### Before
```bash
#!/bin/bash
cd "/root/Aung Chan Myint/Sales-Tele-Bot"
pkill -f "python3 main.py" 2>/dev/null
pkill -f "python3 customer_bot.py" 2>/dev/null
sleep 2
SHEET_ID=... nohup .venv/bin/python3 main.py >> main.log 2>&1 &
...
```
- Old path: `/root/Aung Chan Myint/Sales-Tele-Bot`
- Manually killed + restarted bots via nohup
- No systemd integration

### After
```bash
#!/bin/bash
# PS VIBE — Bot Startup Script (v3.1)
# Updated to use /root/psvibe-sale-bot/ (new location)

cd /root/psvibe-sale-bot

# Try systemd first
systemctl start psvibe-api-server.service 2>/dev/null && echo "API: systemd OK" || echo "API: manual start needed"
systemctl start psvibe-sale-bot.service 2>/dev/null && echo "Sales: systemd OK" || echo "Sales: manual start needed"
systemctl start psvibe-customer.service 2>/dev/null && echo "Customer: systemd OK" || echo "Customer: manual start needed"

sleep 3
echo "---BOTS---"
ps aux | grep python3 | grep -v grep
```

- New path: `/root/psvibe-sale-bot`
- Uses systemd services as primary startup method
- Each service reports OK or "manual start needed" on failure
- Simplified — no inline tokens, no manual nohup process management

## Status
✅ Written and chmod +x on VPS
✅ Verified with cat -n — 14 lines, correct content
