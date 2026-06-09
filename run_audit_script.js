const { Client } = require('ssh2');
const fs = require('fs');
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

// First, write the comprehensive audit script to VPS
const auditScript = `#!/usr/bin/env python3
"""PS VIBE Full System Audit — runs on VPS, outputs JSON for analysis"""
import subprocess, json, os, sys, time

def run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()[:2000] or r.stderr.strip()[:500] or "(empty)"
    except Exception as e:
        return f"ERROR: {e}"

results = {}

# 1. System Info
results['hostname'] = run('uname -a')
results['uptime'] = run('uptime -p')
results['disk'] = run('df -h / | tail -1')
results['memory'] = run('free -h | grep Mem')
results['load'] = run('cat /proc/loadavg')
results['os'] = run('cat /etc/os-release | head -3')

# 2. System Services
results['services'] = run('systemctl list-units --type=service --state=running | grep -iE "psvibe|bot|api"')

# 3. Docker
results['docker_ps'] = run('docker ps --format "{{.Names}}|{{.Status}}|{{.Ports}}"')
results['docker_mysql_check'] = run('docker exec psvibe-mysql mysql -upsvibe_user -pPsVibe@User2024! psvibe_api -e "SELECT COUNT(*) as member_count FROM member_wallets; SELECT COUNT(*) as staff_count FROM staff_records; SELECT COUNT(*) as games FROM games_library; SELECT COUNT(*) as consoles FROM console_status;" 2>&1')
results['docker_mysql_connections'] = run('docker exec psvibe-mysql mysql -upsvibe_user -pPsVibe@User2024! -e "SHOW FULL PROCESSLIST;" 2>&1')
results['docker_mysql_vars'] = run('docker exec psvibe-mysql mysql -upsvibe_user -pPsVibe@User2024! -e "SHOW VARIABLES LIKE \\"%max_connections%\\"; SHOW VARIABLES LIKE \\"%wait_timeout%\\";" 2>&1')

# 4. Running Processes
results['processes'] = run('ps aux | grep python3 | grep -v grep')

# 5. Sales Bot - File Structure
results['sales_files'] = run('find /root/psvibe-sale-bot -maxdepth 2 -type f -name "*.py" | sort')
results['sales_line_count'] = run('wc -l /root/psvibe-sale-bot/main.py /root/psvibe-sale-bot/app.py /root/psvibe-sale-bot/bot/*.py /root/psvibe-sale-bot/handlers/*.py 2>/dev/null')
results['sales_bot_package'] = run('ls /root/psvibe-sale-bot/bot/ 2>/dev/null')
results['sales_bot_init'] = run('cat /root/psvibe-sale-bot/bot/__init__.py 2>/dev/null | head -50')
results['sales_bot_app'] = run('cat /root/psvibe-sale-bot/bot/app.py 2>/dev/null | head -80')
results['sales_keep_alive'] = run('cat /root/psvibe-sale-bot/bot/keep_alive.py 2>/dev/null | head -40')
results['sales_imports'] = run('grep -rn "^import\\|^from" /root/psvibe-sale-bot/bot/__init__.py 2>/dev/null | head -40')
results['sales_imports_handlers'] = run('grep -rn "^import\\|^from" /root/psvibe-sale-bot/handlers/__init__.py 2>/dev/null | head -40')
results['sales_sheets_refs'] = run('grep -rn "gspread\\|sheets\\|sheet\\|spreadsheet\\|SHEET" /root/psvibe-sale-bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -40')
results['sales_mysql_refs'] = run('grep -rn "mysql\\|pymysql\\|mysql.connector\\|sqlalchemy\\|database\\|DB_" /root/psvibe-sale-bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -40')
results['sales_api_refs'] = run('grep -rn "requests\\|httpx\\|aiohttp\\|urllib\\|API_URL\\|api_url\\|API_BASE" /root/psvibe-sale-bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -40')

# 6. Customer Bot - File Structure
results['customer_files'] = run('find /root/psvibe-sale-bot/customer_bot -maxdepth 2 -type f -name "*.py" | sort')
results['customer_line_count'] = run('wc -l /root/psvibe-sale-bot/customer_bot/*.py 2>/dev/null')
results['customer_imports'] = run('grep -rn "^import\\|^from" /root/psvibe-sale-bot/customer_bot/*.py 2>/dev/null | head -50')
results['customer_api_refs'] = run('grep -rn "requests\\|httpx\\|aiohttp\\|urllib\\|API_URL\\|api_url\\|API_BASE\\|API_KEY\\|api_key" /root/psvibe-sale-bot/customer_bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -30')
results['customer_sheets_refs'] = run('grep -rn "gspread\\|sheets\\|sheet\\|spreadsheet\\|SHEET" /root/psvibe-sale-bot/customer_bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -20')
results['customer_data'] = run('ls -la /root/psvibe-sale-bot/customer_bot/data/ 2>/dev/null')
results['customer_handlers'] = run('cat /root/psvibe-sale-bot/customer_bot/handlers.py 2>/dev/null | head -80')

# 7. Wallet Bot - File Structure
results['wallet_files'] = run('find /root/Personal-Wallet-Tele-Bot -maxdepth 3 -type f -name "*.py" | sort')
results['wallet_line_count'] = run('wc -l /root/Personal-Wallet-Tele-Bot/bot/*.py 2>/dev/null')
results['wallet_imports'] = run('grep -rn "^import\\|^from" /root/Personal-Wallet-Tele-Bot/bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -40')
results['wallet_sheets_refs'] = run('grep -rn "gspread\\|sheets\\|sheet\\|spreadsheet\\|SHEET" /root/Personal-Wallet-Tele-Bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -30')
results['wallet_mysql_refs'] = run('grep -rn "mysql\\|pymysql\\|mysql.connector\\|sqlalchemy\\|database\\|DB_" /root/Personal-Wallet-Tele-Bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -20')
results['wallet_api_refs'] = run('grep -rn "requests\\|httpx\\|aiohttp\\|urllib\\|API_URL\\|api_url\\|API_BASE" /root/Personal-Wallet-Tele-Bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -20')
results['wallet_keep_alive'] = run('cat /root/Personal-Wallet-Tele-Bot/bot/keep_alive.py 2>/dev/null | head -30')

# 8. API Server
results['api_files'] = run('ls -la /root/psvibe_api_server/*.py 2>/dev/null')
results['api_config'] = run('cat /root/psvibe_api_server/config.py 2>/dev/null | head -40')
results['api_models'] = run('cat /root/psvibe_api_server/models.py 2>/dev/null | head -50')
results['api_sheets_client'] = run('cat /root/psvibe_api_server/sheets_client.py 2>/dev/null | head -60')
results['api_requirements'] = run('cat /root/psvibe_api_server/requirements.txt 2>/dev/null')
results['api_dockerfile'] = run('cat /root/psvibe_api_server/Dockerfile 2>/dev/null')
results['api_log_errors'] = run('grep -i "error\\|fail\\|exception\\|traceback\\|errno" /root/psvibe_api_server/server.log 2>/dev/null | tail -30')
results['api_log_tail'] = run('tail -30 /root/psvibe_api_server/server.log 2>/dev/null')

# 9. Secrets & Permissions
results['sa_file_exists'] = run('ls -la /root/psvibe_api_server/service_account.json 2>/dev/null | head -1')
results['sa_file_check'] = run('test -s /root/psvibe_api_server/service_account.json && echo "SA_VALID" || echo "SA_EMPTY"')
results['env_perms'] = run('ls -la /root/psvibe-sale-bot/.env 2>/dev/null')
results['secrets_env'] = run('ls -la /etc/psvibe/secrets.env 2>/dev/null; head -5 /etc/psvibe/secrets.env 2>/dev/null | grep -v PASS | grep -v TOKEN | grep -v KEY')
results['venv_packages'] = run('/root/venv/bin/pip3 freeze 2>/dev/null')

# 10. Network & Connectivity
results['port_listen'] = run('ss -tlnp | grep -E "8000|3000|5000|3306|5678|80|443|8080"')
results['telegram_connectivity'] = run('curl -s -o /dev/null -w "%{http_code}" https://api.telegram.org/bot8545665013:AAFgEuw4V_715Q9yzGOYloinIdbdYXYb8zU/getMe 2>/dev/null')

# 11. Journalctl logs
results['journal_sales'] = run('journalctl -u psvibe-sale-bot.service --no-pager -n 30 2>/dev/null')
results['journal_customer'] = run('journalctl -u psvibe_customer_bot.service --no-pager -n 30 2>/dev/null')
results['journal_wallet'] = run('journalctl -u psvibe-wallet.service --no-pager -n 30 2>/dev/null')
results['journal_api'] = run('journalctl -u psvibe-api.service --no-pager -n 30 2>/dev/null')

# 12. Lock files
results['lock_files'] = run('ls -la /tmp/ps_vibe_bot.lock 2>/dev/null; ls -la /tmp/*.lock 2>/dev/null')

# Output as JSON
print(json.dumps(results, indent=2))
`;

const conn = new Client();
conn.on('ready', () => {
  // Write the script to VPS
  conn.exec('cat > /root/run_audit.py << '"'"'SCRIPT'"'"'\n' + auditScript + '\n'"'"'', (err, stream) => {
    if (err) { console.error('Write error:', err.message); conn.end(); return; }
    let out = '';
    stream.on('data', (d) => out += d.toString());
    stream.stderr.on('data', (d) => out += d.toString());
    stream.on('close', (code) => {
      if (code !== 0) console.log('Write result:', out.slice(0,500));
      console.log('Script written to /root/run_audit.py');
      
      // Run it
      conn.exec('cd /root && python3 /root/run_audit.py 2>&1', (err2, stream2) => {
        if (err2) { console.error('Run error:', err2.message); conn.end(); return; }
        let result = '';
        stream2.on('data', (d) => result += d.toString());
        stream2.stderr.on('data', (d) => result += d.toString());
        stream2.on('close', () => {
          fs.writeFileSync('/home/node/.openclaw/workspace/audit_data.json', result);
          console.log('Audit complete. Output saved to audit_data.json');
          conn.end();
        });
      });
    });
  });
});

conn.connect({ host: '5.223.81.16', username: 'root', privateKey: key, readyTimeout: 15000 });
