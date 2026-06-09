#!/usr/bin/env python3
"""Fix PS VIBE VPS: consoleId→console_id + cashback dates."""

import paramiko
import sys
import time

HOST = "5.223.81.16"
USER = "root"
KEY_PATH = "/home/node/.openclaw/workspace/.ssh/id_rsa"

def ssh_connect():
    key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, pkey=key, timeout=15)
    return client

def run(client, cmd, timeout=30):
    """Run a command and return stdout+stderr."""
    print(f"\n[RUN] {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors='replace')
    err = stderr.read().decode(errors='replace')
    exit_code = stdout.channel.recv_exit_status()
    if out:
        print(f"  stdout: {out.strip()}")
    if err:
        print(f"  stderr: {err.strip()}")
    print(f"  exit_code: {exit_code}")
    return out, err, exit_code

def main():
    client = ssh_connect()
    print("✓ Connected to VPS")

    # ───── ISSUE 1: Fix consoleId → console_id ─────
    print("\n" + "="*60)
    print("ISSUE 1: Fix consoleId -> console_id in booking.py")
    print("="*60)

    booking_path = "/root/psvibe-sales-bot/bot/handlers/booking.py"

    # 1a. Read current file (find exact line with consoleId)
    out, _, _ = run(client, f"grep -n 'consoleId' {booking_path}")
    print(f"\n  Lines with consoleId: {out.strip()}")

    # 1b. Make backup
    run(client, f"cp {booking_path} {booking_path}.bak")
    print(f"  ✓ Backup created: {booking_path}.bak")

    # 1c. Replace consoleId with console_id
    out, err, code = run(client, f"sed -i 's/\"consoleId\"/\"console_id\"/g' {booking_path}")

    # 1d. Verify replacement
    out, _, _ = run(client, f"grep -n 'console_id' {booking_path}")
    print(f"\n  Lines with console_id after fix: {out.strip()}")

    # Verify consoleId is gone
    out, _, _ = run(client, f"grep -n 'consoleId' {booking_path}")
    remaining = out.strip()
    if remaining:
        print(f"\n  ⚠️  consoleId STILL PRESENT: {remaining}")
    else:
        print(f"\n  ✓ No more consoleId lines")

    # 1e. Verify Python syntax
    out, err, code = run(client, f"python3 -m py_compile {booking_path}")
    if code == 0:
        print("  ✓ Python syntax OK")
    else:
        print(f"  ✗ Python syntax ERROR (exit {code})")
        print(f"  stderr: {err}")

    # ───── ISSUE 2: Update cashback coupon dates ─────
    print("\n" + "="*60)
    print("ISSUE 2A: Update CASHBACK dates in secrets.env")
    print("="*60)

    env_path = "/etc/psvibe/secrets.env"

    # Show current values
    run(client, f"grep CASHBACK {env_path}")

    # Update each line
    run(client, f"sed -i 's/^CASHBACK_START_DATE=.*/CASHBACK_START_DATE=2026-06-03/' {env_path}")
    run(client, f"sed -i 's/^CASHBACK_END_DATE=.*/CASHBACK_END_DATE=2026-06-07/' {env_path}")
    run(client, f"sed -i 's/^CASHBACK_COUPON_EXPIRY=.*/CASHBACK_COUPON_EXPIRY=2026-06-30/' {env_path}")

    # Verify
    print("\n  Updated values:")
    run(client, f"grep CASHBACK {env_path}")

    # ───── ISSUE 2B: MySQL promotions table ─────
    print("\n" + "="*60)
    print("ISSUE 2B: MySQL promotions table")
    print("="*60)

    mysql_cmd = 'mysql -u root -p"Psvibe@2025" psvibe_api'
    run_opts = {}  # type: ignore

    # Check existing tables
    run(client, f'{mysql_cmd} -e "SHOW TABLES LIKE \'%promo%\';"')

    # Check if promotions exists
    out, _, _ = run(client, f'{mysql_cmd} -e "SHOW TABLES;"')
    if "promotions" in out:
        print("  promotions table EXISTS, checking data...")
        run(client, f'{mysql_cmd} -e "SELECT * FROM promotions;"')

        # Check for cashback_coupon
        out2, _, _ = run(client, f'{mysql_cmd} -e "SELECT * FROM promotions WHERE promo_type=\'cashback_coupon\';"')
        if "cashback_coupon" in out2:
            print("  Found cashback_coupon, UPDATING...")
            run(client, f"""{mysql_cmd} -e "UPDATE promotions SET start_date='2026-06-03', end_date='2026-06-07', coupon_expiry_date='2026-06-30' WHERE promo_type='cashback_coupon';" """)
        else:
            print("  No cashback_coupon row, INSERTING...")
            run(client, f"""{mysql_cmd} -e "INSERT INTO promotions (promo_type, title, description, start_date, end_date, coupon_expiry_date) VALUES ('cashback_coupon', 'Grand Opening Cashback', '100% minute cashback on all sessions during grand opening!', '2026-06-03', '2026-06-07', '2026-06-30');" """)
    else:
        print("  promotions table DOES NOT EXIST, creating...")
        create_sql = """CREATE TABLE IF NOT EXISTS promotions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    promo_type VARCHAR(50),
    title VARCHAR(200),
    description TEXT,
    start_date DATE,
    end_date DATE,
    coupon_expiry_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""
        run(client, f"""{mysql_cmd} -e "{create_sql}" """)

        insert_sql = """INSERT INTO promotions (promo_type, title, description, start_date, end_date, coupon_expiry_date)
VALUES ('cashback_coupon', 'Grand Opening Cashback', '100% minute cashback on all sessions during grand opening!', '2026-06-03', '2026-06-07', '2026-06-30');"""
        run(client, f"""{mysql_cmd} -e "{insert_sql}" """)

    # Verify final promotions data
    print("\n  Final promotions state:")
    run(client, f'{mysql_cmd} -e "SELECT * FROM promotions;"')

    # ───── RESTART BOT ─────
    print("\n" + "="*60)
    print("RESTART: psvibe-sale-bot")
    print("="*60)

    run(client, "systemctl restart psvibe-sale-bot")
    time.sleep(2)

    # Check active
    out, _, _ = run(client, "systemctl is-active psvibe-sale-bot")
    if "active" in out:
        print("  ✓ psvibe-sale-bot is ACTIVE")
    else:
        print(f"  ✗ psvibe-sale-bot status: {out.strip()}")

    # Show recent logs
    print("\n  Recent bot logs:")
    run(client, "journalctl -u psvibe-sale-bot --no-pager -n 10")

    # ───── FINAL SUMMARY ─────
    print("\n" + "="*60)
    print("FINAL VERIFICATION SUMMARY")
    print("="*60)

    print("\n1. Booking.py syntax check:")
    run(client, f"python3 -m py_compile {booking_path}")

    print("\n2. Env cashback values:")
    run(client, f"grep CASHBACK {env_path}")

    print("\n3. Bot status:")
    run(client, "systemctl is-active psvibe-sale-bot")

    print("\n4. MySQL promotions:")
    run(client, f'{mysql_cmd} -e "SELECT * FROM promotions;"')

    client.close()
    print("\n✓ All done. SSH connection closed.")

if __name__ == "__main__":
    main()
