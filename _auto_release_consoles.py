#!/usr/bin/env python3
"""Auto-release consoles when booking end_time has passed.

Runs via cron every 5 minutes.
- Queries console_booking for bookings where end_time < NOW() and status NOT IN ('Done', 'cancelled', 'rejected')
- Updates console_booking.status to 'Done'
- Updates console_status.status to 'Free' for those consoles
"""
import os
import sys
import logging
from datetime import datetime

try:
    import pymysql
except ImportError:
    print("pymysql not installed. Install with: pip install pymysql")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get MySQL connection using pymysql."""

    db_config = {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'psvibe_user',
        'password': '',
        'database': 'psvibe_api',
        'charset': 'utf8mb4',
    }

    # Read environment files for credentials
    for fpath in ('/etc/psvibe/secrets.env', '/root/psvibe-sales-bot/.env'):
        if os.path.exists(fpath):
            with open(fpath) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, _, val = line.partition('=')
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        if key == 'MYSQL_HOST':
                            db_config['host'] = val
                        elif key == 'MYSQL_PORT':
                            db_config['port'] = int(val)
                        elif key == 'MYSQL_USER':
                            db_config['user'] = val
                        elif key == 'MYSQL_PASSWORD':
                            db_config['password'] = val
                        elif key == 'MYSQL_DATABASE':
                            db_config['database'] = val

    if not db_config['password']:
        logger.error("MYSQL_PASSWORD not found in environment files")
        sys.exit(1)

    try:
        conn = pymysql.connect(**db_config)
        return conn
    except Exception as e:
        logger.error("Failed to connect to MySQL: %s", e)
        sys.exit(1)


def release_expired_consoles():
    """Find and release consoles whose booking end_time has passed."""
    conn = get_db_connection()
    released = 0

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # Find bookings past end_time, still active
            sql_find = """
                SELECT id, console_id, member_id, end_time, status
                FROM console_booking
                WHERE end_time < NOW()
                  AND status NOT IN ('Done', 'cancelled', 'rejected')
            """
            cursor.execute(sql_find)
            expired = cursor.fetchall()

            if not expired:
                logger.debug("No expired bookings found")
                return released

            logger.info("Found %d expired booking(s) to release", len(expired))

            for booking in expired:
                bid = booking['id']
                cid = booking['console_id']
                mid = booking.get('member_id', 'N/A')
                et = booking['end_time']
                old_status = booking.get('status', 'N/A')

                logger.info(
                    "Releasing: booking #%d | console=%s | member=%s | end=%s | was=%s",
                    bid, cid, mid, et, old_status
                )

                # Update booking to Done
                cursor.execute(
                    "UPDATE console_booking SET status = 'Done' WHERE id = %s",
                    (bid,)
                )

                # Update console_status to Free
                cursor.execute(
                    "SELECT console_id FROM console_status WHERE console_id = %s",
                    (cid,)
                )
                if cursor.fetchone():
                    cursor.execute(
                        """UPDATE console_status 
                           SET status = 'Free', current_member = NULL, 
                               start_time = NULL, current_game = NULL 
                           WHERE console_id = %s""",
                        (cid,)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO console_status (console_id, status) VALUES (%s, 'Free')",
                        (cid,)
                    )

                released += 1

            conn.commit()
            logger.info("Released %d console(s) successfully", released)

    except Exception as e:
        logger.error("Error releasing consoles: %s", e, exc_info=True)
        conn.rollback()
    finally:
        conn.close()

    return released


if __name__ == '__main__':
    try:
        count = release_expired_consoles()
        logger.info("auto_release_consoles: completed, released=%d", count)
    except Exception as e:
        logger.error("auto_release_consoles: fatal error: %s", e, exc_info=True)
        sys.exit(1)
