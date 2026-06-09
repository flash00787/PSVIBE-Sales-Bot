#!/usr/bin/env python3
"""Fix MySQL promotions table with correct root password."""

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

MYSQL = 'docker exec psvibe-mysql mysql -u root -p"PsVibe@MySQL2024!" psvibe_api'

# Test connection
print("=== Testing connection ===")
run(f'{MYSQL} -e "SELECT 1 AS test;"')

# Check tables
print("\n=== Current tables ===")
run(f'{MYSQL} -e "SHOW TABLES;"')

# Check if promotions exists
print("\n=== Checking promotions ===")
out, _, _ = run(f'{MYSQL} -e "SHOW TABLES LIKE \'%promo%\';"')

if "promotions" in out:
    print("\n=== promotions EXISTS, checking data ===")
    out2, _, _ = run(f'{MYSQL} -e "SELECT * FROM promotions;"')
    
    if "cashback_coupon" in out2:
        print("\n=== UPDATING cashback_coupon ===")
        run(f"""{MYSQL} -e "UPDATE promotions SET start_date='2026-06-03', end_date='2026-06-07', coupon_expiry_date='2026-06-30' WHERE promo_type='cashback_coupon';" """)
    else:
        print("\n=== INSERTING cashback_coupon ===")
        run(f"""{MYSQL} -e "INSERT INTO promotions (promo_type, title, description, start_date, end_date, coupon_expiry_date) VALUES ('cashback_coupon', 'Grand Opening Cashback', '100% minute cashback on all sessions during grand opening!', '2026-06-03', '2026-06-07', '2026-06-30');" """)
else:
    print("\n=== CREATING promotions table ===")
    run(f"""{MYSQL} -e "CREATE TABLE IF NOT EXISTS promotions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    promo_type VARCHAR(50),
    title VARCHAR(200),
    description TEXT,
    start_date DATE,
    end_date DATE,
    coupon_expiry_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);" """)
    
    print("\n=== INSERTING cashback_coupon ===")
    run(f"""{MYSQL} -e "INSERT INTO promotions (promo_type, title, description, start_date, end_date, coupon_expiry_date) VALUES ('cashback_coupon', 'Grand Opening Cashback', '100% minute cashback on all sessions during grand opening!', '2026-06-03', '2026-06-07', '2026-06-30');" """)

# Final verification
print("\n=== FINAL promotions state ===")
run(f'{MYSQL} -e "SELECT * FROM promotions;"')

# Also verify secrets.env one more time
print("\n=== Final env verification ===")
run("grep CASHBACK /etc/psvibe/secrets.env")

# Verify bot still running
print("\n=== Bot status ===")
run("systemctl is-active psvibe-sale-bot")

client.close()
print("\n✓ All done.")
