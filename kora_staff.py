#!/usr/bin/env python3
"""Staff Kora — Quick lookups for PS VIBE staff via CLI.

Usage:
  python3 kora_staff.py free-consoles
  python3 kora_staff.py member <phone>
  python3 kora_staff.py balance <member_id>
  python3 kora_staff.py bookings-today
  python3 kora_staff.py checkin <booking_id>
"""
import sys
from datetime import datetime, timezone, timedelta

# ── Timezone ──────────────────────────────────────────────────
MMT = timezone(timedelta(hours=6, minutes=30))

# ── DB Config ─────────────────────────────────────────────────
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "PsVibe@MySQL2024!",
    "database": "psvibe_api",
    "charset": "utf8mb4",
}


def db():
    import pymysql
    return pymysql.connect(**DB_CONFIG)


# ── Commands ──────────────────────────────────────────────────

def cmd_free_consoles():
    """List free consoles today, plus currently occupied ones."""
    conn = db()
    cur = conn.cursor()

    # Get all console statuses
    cur.execute(
        "SELECT console_id, status, console_type FROM console_status ORDER BY console_id"
    )
    console_status = {row[0]: {"status": row[1], "type": row[2]} for row in cur.fetchall()}

    # Get active/checked_in bookings
    now = datetime.now(MMT)
    cur.execute(
        "SELECT console_id, status, game_name, planned_end, member_id "
        "FROM console_bookings "
        "WHERE booking_date = CURDATE() "
        "AND status IN ('active','checked_in') "
        "ORDER BY planned_start"
    )
    active = {}
    for row in cur.fetchall():
        cid, status, game, pend, member = row
        active[cid] = {
            "status": status,
            "game": game or "N/A",
            "planned_end": pend,
            "member": member or "",
        }

    # Get confirmed (upcoming) bookings
    cur.execute(
        "SELECT console_id, planned_start, game_name "
        "FROM console_bookings "
        "WHERE booking_date = CURDATE() "
        "AND status = 'confirmed' "
        "ORDER BY planned_start"
    )
    upcoming = {}
    for row in cur.fetchall():
        cid, pstart, game = row
        upcoming[cid] = {"planned_start": pstart, "game": game or ""}
    conn.close()

    free_parts = []
    occupied_parts = []
    upcoming_parts = []

    for cid in sorted(console_status.keys()):
        cs = console_status[cid]

        if cid in active:
            a = active[cid]
            remaining = ""
            if a["planned_end"]:
                if a["planned_end"].tzinfo is None:
                    pend_mmt = a["planned_end"].replace(tzinfo=MMT)
                else:
                    pend_mmt = a["planned_end"].astimezone(MMT)
                rem = pend_mmt - now
                if rem.total_seconds() > 0:
                    h = int(rem.total_seconds() // 3600)
                    m = int((rem.total_seconds() % 3600) // 60)
                    remaining = f"{h}h {m}m left"
                else:
                    remaining = "time's up"
            occupied_parts.append(
                f"🔴 {cid}: {a['game']} ({remaining})"
            )
        elif cid in upcoming:
            u = upcoming[cid]
            if u["planned_start"]:
                if u["planned_start"].tzinfo is None:
                    ps_mmt = u["planned_start"].replace(tzinfo=MMT)
                else:
                    ps_mmt = u["planned_start"].astimezone(MMT)
                time_str = ps_mmt.strftime("%H:%M")
            else:
                time_str = "?"
            upcoming_parts.append(
                f"🟡 {cid}: Booked {time_str} ({u['game']})"
            )
        else:
            free_parts.append(f"🟢 {cid}: Free")

    # Output: free first, then upcoming, then occupied
    all_parts = []
    if free_parts:
        all_parts.append(" | ".join(free_parts))
    if upcoming_parts:
        all_parts.append(" | ".join(upcoming_parts))
    if occupied_parts:
        all_parts.append(" | ".join(occupied_parts))

    print("\n".join(all_parts))


def cmd_member(phone):
    """Look up member by phone number."""
    conn = db()
    cur = conn.cursor()

    # Try members table
    cur.execute(
        "SELECT member_id, name, phone, balance_minutes FROM members WHERE phone = %s LIMIT 1",
        (phone,),
    )
    row = cur.fetchone()
    if row:
        mid, name, ph, bal = row

        # Get tier and more info from member_wallets
        cur.execute(
            "SELECT tier, total_spend, join_date, reg_staff FROM member_wallets WHERE member_id = %s",
            (mid,),
        )
        wallet = cur.fetchone()
        tier = "N/A"
        total_spend = 0
        join_date = ""
        staff = ""
        if wallet:
            tier = wallet[0] or "N/A"
            total_spend = wallet[1] or 0
            join_date = str(wallet[2])[:10] if wallet[2] else ""
            staff = wallet[3] or ""

        conn.close()
        print(f"👤 {name or 'Unknown'}")
        print(f"   Card: {mid}")
        print(f"   Phone: {ph}")
        print(f"   Balance: {bal} mins" if bal else "   Balance: 0 mins")
        print(f"   Tier: {tier}")
        if total_spend:
            print(f"   Total Spend: {float(total_spend):,.0f} Ks")
        if join_date:
            print(f"   Member Since: {join_date}")
        if staff:
            print(f"   Registered by: {staff}")
        return

    # Try member_wallets if not found in members
    cur.execute(
        "SELECT member_id, member_name, phone, balance_mins, tier, total_spend, join_date, reg_staff "
        "FROM member_wallets WHERE phone = %s LIMIT 1",
        (phone,),
    )
    row = cur.fetchone()
    conn.close()

    if row:
        mid, name, ph, bal, tier, total_spend, join_date, staff = row
        print(f"👤 {name or 'Unknown'}")
        print(f"   Card: {mid}")
        print(f"   Phone: {ph}")
        print(f"   Balance: {bal} mins" if bal else "   Balance: 0 mins")
        print(f"   Tier: {tier or 'N/A'}")
        if total_spend:
            print(f"   Total Spend: {float(total_spend):,.0f} Ks")
        if join_date:
            print(f"   Member Since: {str(join_date)[:10]}")
        if staff:
            print(f"   Registered by: {staff}")
    else:
        print(f"❌ Member not found for phone: {phone}")


def cmd_balance(member_id):
    """Check member balance by member_id."""
    conn = db()
    cur = conn.cursor()

    cur.execute(
        "SELECT member_name, phone, balance_mins, tier, total_spend "
        "FROM member_wallets WHERE member_id = %s",
        (member_id,),
    )
    row = cur.fetchone()

    if not row:
        cur.execute(
            "SELECT name, phone, balance_minutes FROM members WHERE member_id = %s",
            (member_id,),
        )
        row = cur.fetchone()
        conn.close()
        if row:
            name, phone, bal = row
            print(f"👤 {name or member_id}")
            print(f"   Balance: {float(bal or 0):,.0f} mins")
        else:
            print(f"❌ Member not found: {member_id}")
        return

    name, phone, bal, tier, total_spend = row
    print(f"💰 Balance for {name or member_id}")
    print(f"   Card: {member_id}")
    print(f"   Balance: {int(bal or 0):,} mins")
    print(f"   Tier: {tier or 'N/A'}")
    if total_spend:
        print(f"   Total Spend: {float(total_spend):,.0f} Ks")

    # Recent bookings
    cur2 = conn.cursor()
    cur2.execute(
        "SELECT booking_date, game_name, status, planned_duration_mins "
        "FROM console_bookings WHERE member_id = %s ORDER BY created_at DESC LIMIT 5",
        (member_id,),
    )
    recent = cur2.fetchall()
    if recent:
        print(f"   Recent Sessions:")
        for r in recent:
            bdate, game, status, dur = r
            date_str = str(bdate) if bdate else "?"
            print(f"     {date_str} | {game or 'N/A'} | {status or '?'} | {dur or 0}m")
    conn.close()


def cmd_bookings_today():
    """Today's booking summary."""
    conn = db()
    cur = conn.cursor()
    now = datetime.now(MMT)

    cur.execute(
        "SELECT status, COUNT(*) as cnt "
        "FROM console_bookings WHERE booking_date = CURDATE() "
        "GROUP BY status"
    )
    status_counts = {row[0]: row[1] for row in cur.fetchall()}

    done = status_counts.get("done", 0)
    cancelled = status_counts.get("cancelled", 0)
    active = status_counts.get("active", 0)
    checked_in = status_counts.get("checked_in", 0)
    confirmed = status_counts.get("confirmed", 0)

    # Peak hour
    cur.execute(
        "SELECT HOUR(planned_start) as hr, COUNT(*) as cnt "
        "FROM console_bookings WHERE booking_date = CURDATE() "
        "AND planned_start IS NOT NULL "
        "GROUP BY hr ORDER BY cnt DESC LIMIT 1"
    )
    peak = cur.fetchone()
    peak_str = f"{peak[0]:02d}:00 ({peak[1]} bookings)" if peak else "N/A"

    # Revenue
    cur.execute(
        "SELECT COALESCE(SUM(net), 0) FROM sales_daily WHERE sale_date = CURDATE()"
    )
    revenue = float(cur.fetchone()[0])

    total = sum(status_counts.values())

    print(f"📅 Today: {done} done, {cancelled} cancelled, {active + checked_in} active, {confirmed} confirmed")
    print(f"   Total: {total} bookings")
    print(f"   Revenue: {revenue:,.0f} Ks")
    print(f"   ⏰ Peak: {peak_str}")
    conn.close()


def cmd_checkin(booking_id):
    """Check-in a booking by ID."""
    try:
        bid = int(booking_id)
    except ValueError:
        print(f"❌ Invalid booking ID: {booking_id}")
        return

    conn = db()
    cur = conn.cursor()

    # Get current booking info
    cur.execute(
        "SELECT id, console_id, booking_date, status, game_name, member_id "
        "FROM console_bookings WHERE id = %s",
        (bid,),
    )
    row = cur.fetchone()
    if not row:
        print(f"❌ Booking not found: {bid}")
        conn.close()
        return

    _, cid, bdate, current_status, game, member = row

    if current_status == "checked_in":
        print(f"ℹ️  Booking #{bid} is already checked in ({cid}, {game or 'N/A'})")
        conn.close()
        return

    if current_status == "done":
        print(f"❌ Booking #{bid} is already done")
        conn.close()
        return

    if current_status == "cancelled":
        print(f"❌ Booking #{bid} was cancelled")
        conn.close()
        return

    # Update to checked_in
    cur.execute(
        "UPDATE console_bookings SET status = 'checked_in' WHERE id = %s",
        (bid,),
    )

    # Also update console_status
    cur.execute(
        "UPDATE console_status SET status = 'Occupied', current_game = %s, "
        "current_member = %s, start_time = NOW() WHERE console_id = %s",
        (game, member, cid),
    )
    conn.commit()
    conn.close()

    print(f"✅ Booking #{bid} checked in!")
    print(f"   Console: {cid}")
    print(f"   Game: {game or 'N/A'}")
    if member:
        print(f"   Member: {member}")


# ── Main ──────────────────────────────────────────────────────

USAGE = """Staff Kora — PS VIBE Quick Lookups

Commands:
  free-consoles       List free/occupied consoles today
  member <phone>      Look up member by phone number
  balance <member_id> Check member wallet balance
  bookings-today      Today's booking summary
  checkin <id>        Check-in a booking by ID

Examples:
  python3 kora_staff.py free-consoles
  python3 kora_staff.py member 09976233746
  python3 kora_staff.py balance PSV_A_012
"""


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "free-consoles":
        cmd_free_consoles()
    elif cmd == "member":
        if len(sys.argv) < 3:
            print("❌ Usage: kora_staff.py member <phone>")
            sys.exit(1)
        cmd_member(sys.argv[2])
    elif cmd == "balance":
        if len(sys.argv) < 3:
            print("❌ Usage: kora_staff.py balance <member_id>")
            sys.exit(1)
        cmd_balance(sys.argv[2])
    elif cmd == "bookings-today":
        cmd_bookings_today()
    elif cmd == "checkin":
        if len(sys.argv) < 3:
            print("❌ Usage: kora_staff.py checkin <booking_id>")
            sys.exit(1)
        cmd_checkin(sys.argv[2])
    else:
        print(f"❌ Unknown command: {cmd}")
        print(USAGE)
        sys.exit(1)


if __name__ == "__main__":
    main()
