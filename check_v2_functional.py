#!/usr/bin/env python3
"""Systematic functional check of V.2 — verify ALL critical functions can be imported"""
import subprocess, json, sys

# SSH command template
HOST = "167.71.196.120"
def ssh(cmd):
    import os
    # Use sshpass to avoid password in cmdline
    result = subprocess.run(
        ["sshpass", "-p", "Freedom2024#RevFlash", "ssh", "-o", "StrictHostKeyChecking=no", f"root@{HOST}", cmd],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout, result.stderr

print("=" * 70)
print("V.2 — COMPREHENSIVE FUNCTIONAL CHECK")
print("=" * 70)

# 1. Service status
out, err = ssh("systemctl is-active psvibe-bot-refactored")
print(f"\n📦 Service: {out.strip()}")

# 2. PID + uptime
out, err = ssh("ps -p $(systemctl show -p MainPID psvibe-bot-refactored 2>/dev/null | cut -d= -f2) -o pid,etimes --no-headers 2>/dev/null")
print(f"PID: {out.strip() if out.strip() else '(checking...)'}")

# 3. Memory
out, err = ssh('ps aux | grep python3 | grep -v grep | head -5 | awk \'{print $2 " " $6/1024 " MB " $11}\'')
print("Memory:")
for line in out.strip().split('\n'):
    print(f"  {line}")

# 4. Log tail
out, err = ssh("tail -20 /root/Sales-Tele-Bot_refactored/logs/bot.log")
print("\n📋 LOG (last 20 lines):")
for line in out.strip().split('\n'):
    print(f"  {line}")

# 5. Import test — verify critical modules
print("\n🔬 CRITICAL MODULE IMPORT TEST:")
import_checks = [
    "from bot import main, keep_alive, ensure_sheet_headers",
    "from bot.handlers import *",
    "from bot.handlers.console import *",
    "from bot.handlers.booking import *",
    "from bot.handlers.games import *",
    "from bot.handlers.stock import *",
    "from bot.handlers.sales import *",
    "from bot.handlers.main_menu import *",
]

for check in import_checks:
    py_cmd = f'cd /root/Sales-Tele-Bot_refactored && python3 -c "{check}; print(\'OK: {check}\')" 2>&1'
    out, err = ssh(py_cmd)
    if "OK:" in out:
        print(f"  ✅ {check}")
    else:
        err_short = out.strip().split('\n')[-1] if out.strip() else "unknown error"
        print(f"  ❌ {check}: {err_short}")

# 6. Check for NameErrors in running bot
print("\n🎯 NAMEERROR CHECK (running bot log):")
out, err = ssh("grep -i 'NameError\\|KeyError\\|AttributeError' /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null")
if out.strip():
    for line in out.strip().split('\n')[-5:]:
        print(f"  ❌ {line}")
else:
    print("  ✅ No NameError/KeyError in log")

# 7. Template render check
print("\n📄 TEMPLATE RENDER CHECK:")
for sym in ["show_main_menu", "prompt_book_console", "show_game_menu", "prompt_member", "cmd_inventory"]:
    py_cmd = f'cd /root/Sales-Tele-Bot_refactored && python3 -c "from bot.handlers import *; print({sym})" 2>&1'
    out, err = ssh(py_cmd)
    if "function" in out or "class" in out:
        print(f"  ✅ {sym} → {out.strip()[:60]}")
    elif "<built-in" in out or "object" in out:
        print(f"  ✅ {sym} → {out.strip()[:60]}")
    else:
        err_short = out.strip().replace('\n', ' | ')[:120] if out.strip() else "???"
        print(f"  ❌ {sym}: {err_short}")

print("\n" + "=" * 70)
print("CHECK COMPLETE")
print("=" * 70)
