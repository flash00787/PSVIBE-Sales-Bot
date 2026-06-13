#!/usr/bin/env python3
"""
PS VIBE — Booking Reminder Cron Script
======================================
Runs every 15 minutes via cron.
Checks console_booking table for bookings starting in ~1 hour.
Sends Telegram reminder to customer using CUSTOMER_BOT_TOKEN.
Uses message_thread_id pattern from existing bot infrastructure.

Integrates with /root/psvibe-sales-bot/.env and /etc/psvibe/secrets.env
for credentials.
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta, timezone

# ── Config ────────────────────────────────────────────────────────────────────
MMT = timezone(timedelta(hours=6, minutes=30))
STAFF_NOTIFY_CHAT = "-1003686032747"
TRACK_FILE = "/root/psvibe-sales-bot/data/booking_reminders.json"
MESSAGE_THREAD_ID = 125192  # Default thread ID used by existing reminders

# Load env vars
ENV_FILE = "/root/psvibe-sales-bot/.env"
SECRETS_FILE = "/etc/psvibe/secrets.env"

def _load_env_file(filepath):
    if not os.path.isfile(filepath):
        return
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:]
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val

_load_env_file(ENV_FILE)
_load_env_file(SECRETS_FILE)

CUSTOMER_BOT_TOKEN = os.environ.get("CUSTOMER_BOT_TOKEN", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ── MySQL Query via Docker ────────────────────────────────────────────────────
def sql(query):
    cmd = [
        "docker", "exec", "psvibe-mysql",
        "mysql", "-upsvibe_user", "-pPsVibe@2026_Rotated!",
        "psvibe_api", "-N", "-B", "-e", query
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception as e:
        print(f"SQL ERROR: {e}", file=sys.stderr)
        return None


def tg_send(chat_id, text, token=None, parse_mode="HTML", message_thread_id=None):
    """Send Telegram message via Bot API."""
    import requests
    token = token or CUSTOMER_BOT_TOKEN
    if not token or not chat_id:
        return False
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    if message_thread_id:
        payload["message_thread_id"] = message_thread_id
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json=payload,
            timeout=15,
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"Telegram send error: {e}", file=sys.stderr)
        return False


# ── Track sent reminders to avoid duplicates ──────────────────────────────────
def load_track():
    if not os.path.isfile(TRACK_FILE):
        return {}
    try:
        with open(TRACK_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_track(data):
    os.makedirs(os.path.dirname(TRACK_FILE), exist_ok=True)
    with open(TRACK_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── Main ──────────────────────────────────────────────────────────────────────
def check_and_remind():
    now_mmt = datetime.now(MMT)
    now_iso = now_mmt.isoformat()
    
    # Find bookings starting in 45-75 minutes from now (cover the ~1 hour window)
    window_start = (now_mmt + timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S")
    window_end = (now_mmt + timedelta(minutes=75)).strftime("%Y-%m-%d %H:%M:%S")
    
    query = f"""
    SELECT 
        id, 
        console_id, 
        member_id, 
        start_time, 
        end_time, 
        duration_mins,
        game_name,
        telegram_chat_id,
        phone,
        status
    FROM console_booking 
    WHERE status IN ('confirmed', 'pending')
      AND start_time >= '{window_start}'
      AND start_time <= '{window_end}'
    ORDER BY start_time ASC
    """
    
    result = sql(query)
    
    if not result:
        print(f"[{now_iso}] No bookings found in reminder window")
        return
    
    bookings = []
    for line in result.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 10:
            bookings.append({
                "id": parts[0],
                "console_id": parts[1],
                "member_id": parts[2],
                "start_time": parts[3],
                "end_time": parts[4],
                "duration_mins": parts[5],
                "game_name": parts[6],
                "telegram_chat_id": parts[7],
                "phone": parts[8],
                "status": parts[9],
            })
    
    if not bookings:
        print(f"[{now_iso}] No bookings in reminder window")
        return
    
    # Load tracking data
    track = load_track()
    today_key = now_mmt.strftime("%Y-%m-%d")
    
    sent_count = 0
    for bk in bookings:
        bk_id = str(bk["id"])
        
        # Skip if already sent reminder for this booking today
        if bk_id in track.get(today_key, {}):
            continue
        
        # Parse start time
        try:
            start_dt = datetime.strptime(bk["start_time"], "%Y-%m-%d %H:%M:%S")
            start_display = start_dt.strftime("%I:%M %p")
        except (ValueError, TypeError):
            start_display = bk["start_time"]
        
        chat_id = bk["telegram_chat_id"]
        game = bk["game_name"] or "N/A"
        console = bk["console_id"] or "PS Console"
        duration = bk["duration_mins"] or "N/A"
        
        # ── Send reminder to customer ──
        if chat_id:
            cust_msg = (
                "⏰ <b>Booking Reminder — PS VIBE</b>\n\n"
                f"သင့် Booking သည် <b>၁ နာရီအတွင်း</b> စတင်ပါမည်။\n\n"
                f"🕹️ Console : <b>{console}</b>\n"
                f"🎮 Game    : <b>{game}</b>\n"
                f"⏱️ Duration: <b>{duration} မိနစ်</b>\n"
                f"🕐 Time    : <b>{start_display}</b> MMT\n\n"
                "📍 No. 17, Mau Pin Street, Sanchaung, Yangon\n\n"
                "⏳ အချိန်မှီ လာရောက်ပေးပါရန် မေတ္တာရပ်ခံအပ်ပါသည်။\n"
                "🙏 ကျေးဇူးတင်ပါတယ် — <i>PS VIBE Team</i>"
            )
            ok = tg_send(
                chat_id, cust_msg,
                token=CUSTOMER_BOT_TOKEN,
                message_thread_id=MESSAGE_THREAD_ID if MESSAGE_THREAD_ID else None,
            )
            if ok:
                sent_count += 1
                print(f"[{now_iso}] ✅ Reminder sent to chat_id={chat_id} for booking #{bk_id}")
            else:
                print(f"[{now_iso}] ❌ Failed to send reminder to chat_id={chat_id}", file=sys.stderr)
        else:
            print(f"[{now_iso}] ⚠️ No telegram_chat_id for booking #{bk_id}, skipping")
        
        # Track this reminder
        if today_key not in track:
            track[today_key] = {}
        track[today_key][bk_id] = {
            "sent_at": now_iso,
            "booking_id": bk_id,
            "member_id": bk["member_id"],
        }
    
    # Save tracking data
    save_track(track)
    
    # ── Notify staff channel ──
    if sent_count > 0 and STAFF_NOTIFY_CHAT:
        staff_msg = (
            f"🔔 <b>Booking Reminders Sent</b>\n"
            f"📅 {now_mmt.strftime('%d %b %Y %I:%M %p')} MMT\n"
            f"📨 {sent_count} reminder(s) sent for bookings in ~1 hour"
        )
        tg_send(STAFF_NOTIFY_CHAT, staff_msg, token=BOT_TOKEN or CUSTOMER_BOT_TOKEN)
    
    print(f"[{now_iso}] Done. {sent_count} reminder(s) sent.")


if __name__ == "__main__":
    check_and_remind()
