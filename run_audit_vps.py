#!/usr/bin/env python3
"""PS VIBE Full System Audit — outputs JSON for analysis"""
import subprocess, json, os

def run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout.strip()[:3000] or r.stderr.strip()[:500] or "(empty)")
    except Exception as e:
        return f"ERROR: {e}"

results = {}

results['hostname'] = run('uname -a')
results['uptime'] = run('uptime -p')
results['disk'] = run('df -h / | tail -1')
results['memory'] = run('free -h | grep Mem')
results['load'] = run('cat /proc/loadavg')
results['os'] = run('cat /etc/os-release | head -3')

results['services'] = run('systemctl list-units --type=service --state=running | grep -iE "psvibe|bot|api"')
results['docker_ps'] = run('docker ps --format "{{.Names}}|{{.Status}}|{{.Ports}}"')
results['docker_mysql_tables'] = run('docker exec psvibe-mysql mysql -upsvibe_user -pPsVibe@User2024! psvibe_api -e "SELECT COUNT(*) as members FROM member_wallets; SELECT COUNT(*) as staff FROM staff_records; SELECT COUNT(*) as games FROM games_library; SELECT COUNT(*) as consoles FROM console_status;" 2>&1')
results['docker_mysql_connections'] = run('docker exec psvibe-mysql mysql -upsvibe_user -pPsVibe@User2024! -e "SHOW FULL PROCESSLIST;" 2>&1')
results['processes'] = run('ps aux | grep python3 | grep -v grep')

results['sales_files'] = run('find /root/psvibe-sale-bot -maxdepth 2 -type f -name "*.py" | sort')
results['sales_sheets_refs'] = run('grep -rn "gspread\\|sheets\\|sheet\\|spreadsheet\\|SHEET" /root/psvibe-sale-bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -40')
results['sales_mysql_refs'] = run('grep -rn "mysql\\|pymysql\\|mysql.connector\\|sqlalchemy\\|DB_HOST\\|DB_USER\\|DB_PASS" /root/psvibe-sale-bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -40')
results['sales_api_refs'] = run('grep -rn "requests\\|httpx\\|aiohttp\\|urllib\\|API_URL\\|api_url\\|API_BASE" /root/psvibe-sale-bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -40')
results['sales_bot_init'] = run('cat /root/psvibe-sale-bot/bot/__init__.py 2>/dev/null')
results['sales_bot_app'] = run('cat /root/psvibe-sale-bot/bot/app.py 2>/dev/null')

results['customer_files'] = run('find /root/psvibe-sale-bot/customer_bot -maxdepth 2 -type f -name "*.py" | sort')
results['customer_line_count'] = run('wc -l /root/psvibe-sale-bot/customer_bot/*.py 2>/dev/null')
results['customer_imports'] = run('head -80 /root/psvibe-sale-bot/customer_bot/handlers.py 2>/dev/null')
results['customer_ai'] = run('head -60 /root/psvibe-sale-bot/customer_bot/ai.py 2>/dev/null')
results['customer_api'] = run('head -60 /root/psvibe-sale-bot/customer_bot/api.py 2>/dev/null')
results['customer_sheets_refs'] = run('grep -rn "gspread\\|sheets\\|sheet\\|spreadsheet" /root/psvibe-sale-bot/customer_bot/ 2>/dev/null | grep -v __pycache__ | head -20')

results['wallet_files'] = run('find /root/Personal-Wallet-Tele-Bot -maxdepth 3 -type f -name "*.py" | sort')
results['wallet_sheets_refs'] = run('grep -rn "gspread\\|sheets\\|sheet\\|spreadsheet" /root/Personal-Wallet-Tele-Bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -30')
results['wallet_mysql_refs'] = run('grep -rn "mysql\\|pymysql\\|sqlalchemy\\|database" /root/Personal-Wallet-Tele-Bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -20')

results['api_config'] = run('cat /root/psvibe_api_server/config.py 2>/dev/null')
results['api_models'] = run('cat /root/psvibe_api_server/models.py 2>/dev/null')
results['api_sheets_client_head'] = run('head -80 /root/psvibe_api_server/sheets_client.py 2>/dev/null')
results['api_requirements'] = run('cat /root/psvibe_api_server/requirements.txt 2>/dev/null')
results['api_log_errors'] = run('grep -i "error\\|fail\\|exception\\|traceback\\|errno" /root/psvibe_api_server/server.log 2>/dev/null | tail -30')
results['api_log_tail'] = run('tail -30 /root/psvibe_api_server/server.log 2>/dev/null')

results['sa_file'] = run('ls -la /root/psvibe_api_server/service_account.json 2>/dev/null; test -s /root/psvibe_api_server/service_account.json && echo "VALID" || echo "EMPTY"')
results['env_perms'] = run('ls -la /root/psvibe-sale-bot/.env 2>/dev/null')
results['port_listen'] = run('ss -tlnp | grep -E "8000|3000|5000|3306|5678|80|443|8080"')
results['telegram_test'] = run('curl -s -o /dev/null -w "%{http_code}" https://api.telegram.org/bot8545665013:AAFgEuw4V_715Q9yzGOYloinIdbdYXYb8zU/getMe 2>/dev/null')

results['journal_api'] = run('journalctl -u psvibe-api.service --no-pager -n 30 2>/dev/null')
results['journal_sales'] = run('journalctl -u psvibe-sale-bot.service --no-pager -n 30 2>/dev/null')
results['journal_customer'] = run('journalctl -u psvibe_customer_bot.service --no-pager -n 30 2>/dev/null')
results['journal_wallet'] = run('journalctl -u psvibe-wallet.service --no-pager -n 30 2>/dev/null')

results['lock_files'] = run('ls -la /tmp/*.lock 2>/dev/null')

print(json.dumps(results, indent=2))
