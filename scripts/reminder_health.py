#!/usr/bin/env python3
"""
Reminder Health Monitor — Check if session reminders are actually being
processed. If active reminders exist in the store but no reminder activity
is seen recently, auto-restart the sale bot and alert staff.

Usage:
    python3 scripts/reminder_health.py                    # Single check
    python3 scripts/reminder_health.py --alert-only       # Alert only, no restart
    python3 scripts/reminder_health.py --daemon            # Continuous loop

Thresholds:
    - If active reminders exist but NO reminder log activity in 20 min → WARNING
    - If reminder store has entries older than 30 min (stuck) → CRITICAL → restart
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
REMINDER_FILE = "/root/psvibe-sales-bot/data/session_reminders.json"
NOTIFIER = "/root/coordination/notifier.py"
SERVICE = "psvibe-sale-bot"
LOG_FILE = "/var/log/reminder_health.log"
IDLE_WARN_MINUTES = 20       # Warn if active reminders + no log activity in X min
STUCK_CRITICAL_MINUTES = 30  # Critical if entries exist but are this old
CHECK_INTERVAL_SEC = 600      # Daemon check interval (10 min)

# Log patterns that indicate the reminder system is alive and processing
ALIVE_PATTERNS = [
    "reminder_sent:",           # Reminder actually sent to chat
    "reminder_store removed",    # Reminder completed normally
    "reminder_store restoring",  # Reminder restored on startup
    "cleanup_stale: purged",     # Stale entries cleaned up
]

# Error patterns that indicate a problem
ERROR_PATTERNS = [
    "_remind_loop:",
    "remind.*Error",
    "remind.*error",
    "get_customer_chat_id.*not defined",
    "NameError",
    "ImportError",
]


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] {msg}"
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")
    print(line)


def read_reminders() -> dict:
    """Read active reminders from the JSON store."""
    try:
        if not os.path.isfile(REMINDER_FILE):
            return {}
        with open(REMINDER_FILE, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as e:
        log(f"⚠️ Cannot read reminder file: {e}")
        return {}


def get_active_reminders(store: dict) -> dict:
    """Filter to only active (non-expired) reminders."""
    now = datetime.now(timezone.utc)
    active = {}
    for key, entry in store.items():
        updated = entry.get("updated_at", "")
        if updated:
            try:
                dt = datetime.fromisoformat(updated)
                age_min = (now - dt).total_seconds() / 60
                # Keep entries updated within last 4 hours
                if age_min < 240:
                    active[key] = entry
            except (ValueError, TypeError):
                pass
    return active


def check_log_activity(minutes: int) -> tuple:
    """Check journalctl for reminder activity in the last N minutes.
    Returns (alive_count, error_count, sample_line).
    """
    alive = 0
    errors = 0
    sample = ""

    try:
        # Check alive patterns
        for pattern in ALIVE_PATTERNS:
            cmd = (
                f"journalctl -u {SERVICE} --since '{minutes} min ago' --no-pager 2>&1 "
                f"| grep -c '{pattern}' || true"
            )
            rc, out, err = run(cmd)
            try:
                alive += int(out.strip())
            except ValueError:
                pass

        # Check error patterns
        for pattern in ERROR_PATTERNS:
            cmd = (
                f"journalctl -u {SERVICE} --since '{minutes} min ago' --no-pager 2>&1 "
                f"| grep -i '{pattern}' | tail -3 || true"
            )
            rc, out, err = run(cmd)
            if out.strip():
                errors += 1
                sample = out.strip().split("\n")[-1] if out.strip() else ""

    except Exception as e:
        log(f"⚠️ Log check error: {e}")

    return alive, errors, sample


def send_alert(title: str, message: str, level: str = "warning") -> bool:
    """Send notification via notifier.py."""
    try:
        subprocess.run(
            [sys.executable, NOTIFIER, "send",
             "--title", title,
             "--message", message,
             "--level", level],
            capture_output=True, timeout=15,
        )
        return True
    except Exception as e:
        log(f"⚠️ Alert send failed: {e}")
        return False


def restart_bot() -> bool:
    """Restart the sale bot service."""
    log("🔄 Restarting psvibe-sale-bot...")
    rc, out, err = run(f"systemctl restart {SERVICE}")
    time.sleep(5)
    rc2, status, _ = run(f"systemctl is-active {SERVICE}")
    success = rc2 == 0
    log(f"   Restart {'✅ OK' if success else '❌ FAILED'}: {status}")
    return success


def run(cmd: str):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Timed out"
    except Exception as e:
        return -1, "", str(e)


def single_check(alert_only: bool = False):
    """Run one health check cycle. Returns 0 if healthy, 1 if issues."""
    store = read_reminders()
    active = get_active_reminders(store)
    active_count = len(active)
    total_count = len(store)

    log(f"Store: {total_count} total, {active_count} active")

    # Check bot is running
    rc, status, _ = run(f"systemctl is-active {SERVICE}")
    bot_alive = rc == 0

    if not bot_alive:
        log(f"🔴 {SERVICE} is NOT running!")
        send_alert("🚨 Sale Bot DOWN", f"{SERVICE} is not active", "danger")
        if not alert_only:
            restart_bot()
        return 1

    # No active reminders — nothing to worry about
    if active_count == 0:
        log("✅ No active reminders — system healthy")
        return 0

    # Active reminders exist — check log activity
    alive_count, error_count, error_sample = check_log_activity(IDLE_WARN_MINUTES)

    log(f"Log activity (last {IDLE_WARN_MINUTES}min): {alive_count} alive, {error_count} errors")

    # Get oldest entry for stuck detection
    now = datetime.now(timezone.utc)
    oldest_age = 0
    for entry in active.values():
        updated = entry.get("updated_at", "")
        if updated:
            try:
                dt = datetime.fromisoformat(updated)
                age = (now - dt).total_seconds() / 60
                oldest_age = max(oldest_age, age)
            except (ValueError, TypeError):
                pass

    # ── CRITICAL: Entries are stuck (old but no activity) ──
    if oldest_age > STUCK_CRITICAL_MINUTES and alive_count == 0:
        console_ids = [e.get("cid", "?") for e in active.values()]
        msg = (
            f"🔴 Reminders STUCK! {active_count} entries, oldest {oldest_age:.0f}min old.\n"
            f"Consoles: {', '.join(console_ids)}\n"
            f"Bot process alive but reminders not processing.\n"
            f"Action: {'ALERT ONLY' if alert_only else 'AUTO-RESTARTING bot'}"
        )
        log(msg)
        if error_count > 0:
            log(f"   Error sample: {error_sample}")
        send_alert("🚨 Reminder System STUCK", msg, "danger")

        if not alert_only:
            success = restart_bot()
            if success:
                log("✅ Bot restarted — reminders should restore on startup")
                send_alert(
                    "✅ Bot Restarted",
                    f"Auto-restart done. Reminders should restore. Consoles: {', '.join(console_ids)}",
                    "info",
                )
            else:
                send_alert(
                    "🔴 Bot Restart FAILED",
                    f"Manual intervention needed! {SERVICE} won't restart. Consoles: {', '.join(console_ids)}",
                    "danger",
                )
        return 1

    # ── WARNING: Active reminders but no recent log activity ──
    if alive_count == 0 and oldest_age > 10:
        console_ids = [e.get("cid", "?") for e in active.values()]
        msg = (
            f"⚠️ Reminder log SILENT for {IDLE_WARN_MINUTES}min with {active_count} active reminders.\n"
            f"Consoles: {', '.join(console_ids)}\n"
            f"May be normal if no reminders have fired yet."
        )
        log(msg)
        # Only alert once per hour max (track via temp file)
        alert_tracker = "/tmp/reminder_health_warned"
        should_alert = True
        if os.path.exists(alert_tracker):
            try:
                mtime = os.path.getmtime(alert_tracker)
                if time.time() - mtime < 3600:
                    should_alert = False
            except OSError:
                pass
        if should_alert:
            send_alert("⚠️ Reminder System Silent", msg, "warning")
            Path(alert_tracker).touch()
        return 1

    # ── Error detected but reminders still processing ──
    if error_count > 0:
        console_ids = [e.get("cid", "?") for e in active.values()]
        log(f"⚠️ {error_count} reminder errors detected (but system still alive)")
        send_alert(
            "⚠️ Reminder Errors",
            f"{error_count} errors in reminder system. Consoles: {', '.join(console_ids)}\n"
            f"Sample: {error_sample[:200] if error_sample else 'N/A'}",
            "warning",
        )
        return 1

    # All good
    log(f"✅ Healthy: {active_count} active reminders, {alive_count} recent log events")

    # Clean up warning tracker if healthy
    alert_tracker = "/tmp/reminder_health_warned"
    if os.path.exists(alert_tracker):
        os.remove(alert_tracker)

    return 0


def main():
    alert_only = "--alert-only" in sys.argv
    daemon = "--daemon" in sys.argv

    if daemon:
        log("🚀 Reminder Health Monitor daemon started")
        log(f"   Check interval: {CHECK_INTERVAL_SEC}s")
        log(f"   Idle warn: {IDLE_WARN_MINUTES}min | Stuck critical: {STUCK_CRITICAL_MINUTES}min")
        while True:
            try:
                single_check(alert_only=alert_only)
            except Exception as e:
                log(f"🔴 Monitor error: {e}")
            time.sleep(CHECK_INTERVAL_SEC)
    else:
        sys.exit(single_check(alert_only=alert_only))


if __name__ == "__main__":
    main()
