"""Kora Dashboard — Command Execution Routes"""
import logging
import subprocess
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kora", tags=["Kora"])

ALLOWED_COMMANDS = {
    "health": "uptime && echo '---' && free -h | head -2 && echo '---Disk:' && df -h / | tail -1",
    "mysql_health": "curl -s --connect-timeout 5 http://127.0.0.1:8000/api/mysql/health",
    "uptime": "uptime && echo '---Memory:' && free -h | head -2",
    "disk": "df -h / | tail -1 && echo '---Inodes:' && df -i / | tail -1",
    "docker": "docker ps --format 'table {{.Names}}\t{{.Status}}' 2>/dev/null | head -20",
    "services": "docker ps --format '{{.Names}}: {{.Status}}' 2>/dev/null",
    "mem": "free -h && echo '---CPU:' && top -bn1 | grep 'Cpu(s)' | head -1",
    "process": "ps aux --sort=-%mem | head -10",
    "backup": "echo 'Backups:' && ls -lh /root/.openclaw/workspace/backups/ 2>/dev/null | tail -5 || echo '(no backups directory)'",
    "alerts": "echo 'Kora Health Status' && curl -s --connect-timeout 5 http://127.0.0.1:8000/api/mysql/health 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(\"MySQL:\", \"Connected\" if d.get(\"mysql_connected\") else \"Disconnected\")' 2>/dev/null || echo 'Health check unavailable'",
}


@router.get("/cmd/{command}")
async def run_kora_command(command: str):
    """Execute allowed Kora commands and return output"""
    if command not in ALLOWED_COMMANDS:
        return {
            "success": False,
            "command": command,
            "error": f"Unknown command. Allowed: {list(ALLOWED_COMMANDS.keys())}"
        }

    try:
        result = subprocess.run(
            ALLOWED_COMMANDS[command],
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "success": True,
            "command": command,
            "output": result.stdout.strip() or "(no output)",
            "error": result.stderr.strip() if result.stderr.strip() else None
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "command": command, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "command": command, "error": str(e)}
