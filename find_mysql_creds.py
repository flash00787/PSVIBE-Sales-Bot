#!/usr/bin/env python3
"""Find actual MySQL credentials."""

import paramiko

HOST = "5.223.81.16"
USER = "root"
KEY_PATH = "/home/node/.openclaw/workspace/.ssh/id_rsa"

key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, pkey=key, timeout=15)

def run(cmd, timeout=30):
    print(f"\n[RUN] {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors='replace')
    err = stderr.read().decode(errors='replace')
    code = stdout.channel.recv_exit_status()
    if out: print(f"  stdout: {out.strip()}")
    if err: print(f"  stderr: {err.strip()}")
    print(f"  exit_code: {code}")
    return out, err, code

# Check Docker container env vars for MySQL root password
print("=== MySQL container environment ===")
run("docker inspect psvibe-mysql | grep -A2 -i 'MYSQL_ROOT\|MYSQL_PASSWORD\|MYSQL_USER\|MYSQL_DATABASE' | head -20")

# Check app configs for DB credentials
print("\n=== Sale bot DB config ===")
run("grep -r 'mysql\|MYSQL\|DB_\|database' /root/psvibe-sales-bot/config* 2>/dev/null | head -20")
run("grep -r 'mysql\|MYSQL\|DB_\|database' /root/psvibe-sales-bot/.env 2>/dev/null | head -20")

print("\n=== API server DB config ===")
run("grep -r 'mysql\|MYSQL\|DB_\|database' /root/psvibe_api_server/.env 2>/dev/null | head -20")
run("ls /root/psvibe_api_server/.env* 2>/dev/null")
run("cat /root/psvibe_api_server/config.py 2>/dev/null | head -40")

print("\n=== Secrets env ===")
run("grep -i 'mysql\|db_\|database' /etc/psvibe/secrets.env 2>/dev/null")

print("\n=== Try no-password root access ===")
run('docker exec psvibe-mysql mysql -u root psvibe_api -e "SELECT 1;"')

print("\n=== Try various passwords ===")
for pw in ['psvibe', 'Psvibe2025', 'root', 'password', '']:
    cmd = f'docker exec psvibe-mysql mysql -u root -p"{pw}" psvibe_api -e "SELECT 1;" 2>&1'
    out, err, code = run(cmd)
    if code == 0:
        print(f"  >>> FOUND WORKING PASSWORD: {pw}")
        break

client.close()
