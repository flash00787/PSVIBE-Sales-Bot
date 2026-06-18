#!/usr/bin/env python3
"""Auto-cancel bookings where customer hasn't checked in within 15 mins of start time.
Sends Telegram notifications to both customer and staff chat.

FIXED (2026-06-03):
  - Load env vars from /etc/psvibe/secrets.env
  - Use correct env var names (API_KEY, BOT_TOKEN, CUSTOMER_BOT_TOKEN, STAFF_NOTIFY_CHAT)
  - Send Telegram notifications on auto-cancel (customer + staff)
  - Handle past-day stale bookings (not just today)
  - Fix deprecated datetime.utcnow() → datetime.now(datetime.UTC)
  - Proper MMT timezone handling
"""
import requests
import json
import os
import sys
from datetime import datetime, timedelta, timezone

# ── Load env vars ──────────────────────────────────────────────────────────────
SECRETS_FILE = "/etc/psvibe/secrets.env"
ENV_FILE = "/root/psvibe-sales-bot/.env"

TRACK_FILE = "/root/psvibe-sales-bot/data/booking_reminders.json"

def _load_env_file(filepath):
    """Load key=value pairs from an env file (simple parser, handles exports)."""
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

API_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_KEY = os.environ.get("API_KEY", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CUSTOMER_BOT_TOKEN = os.environ.get("CUSTOMER_BOT_TOKEN", "")
STAFF_NOTIFY_CHAT = os.environ.get("STAFF_NOTIFY_CHAT", "")
MMT = timezone(timedelta(hours=6, minutes=30))


def tg_send(to_chat_id, text, token=None, parse_mode="HTML"):
    if not token:
        token = CUSTOMER_BOT_TOKEN
    if not token or not to_chat_id:
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": to_chat_id, "text": text, "parse_mode": parse_mode},
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False


def auto_cancel():
    now_utc = datetime.now(timezone.utc)
    now_mmt = datetime.now(MMT)
    
    headers = {"X-API-Key": API_KEY}
    
    all_bookings = []
    
    for status_filter in ("confirmed", "pending"):
        try:
            resp = requests.get(
                f"{API_URL}/api/bookings",
                params={"status": status_filter},
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    inner = data.get("data", data)
                    if isinstance(inner, dict):
                        all_bookings.extend(inner.get("bookings", []))
                    elif isinstance(inner, list):
                        all_bookings.extend(inner)
                elif isinstance(data, list):
                    all_bookings.extend(data)
        except Exception as e:
            print(f"Error fetching {status_filter} bookings: {e}")
    
    if not all_bookings:
        print(f"{now_mmt.strftime('%Y-%m-%d %H:%M')} MMT — No bookings to check")
        return
    
    # De-duplicate by ID
    seen = set()
    unique = []
    for b in all_bookings:
        bid = b.get("id")
        if bid and bid not in seen:
            seen.add(bid)
            unique.append(b)
    all_bookings = unique
    
    print(f"{now_mmt.strftime('%Y-%m-%d %H:%M')} MMT — Checking {len(all_bookings)} bookings for auto-cancel")
    
    cancelled = 0
    notified_customers = 0
    notified_staff = 0
    
    for b in all_bookings:
        status = (b.get("status") or "").lower()
        if status not in ("confirmed", "pending"):
            continue
        
        time_slot = b.get("timeSlot") or b.get("startTime") or ""
        bk_date = b.get("date") or b.get("booking_date") or ""
        
        if not time_slot or not bk_date:
            continue
        
        time_str = str(time_slot)
        if "T" in time_str:
            time_str = time_str.split("T")[1][:5]
        if " " in time_str:
            parts = time_str.split(" ")
            time_str = parts[1][:5] if len(parts) > 1 and ":" in parts[1] else parts[0][:5]
        
        try:
            h, m = map(int, time_str.split(":"))
        except (ValueError, AttributeError):
            continue
        
        try:
            bk_date_clean = str(bk_date).split(" ")[0]
            booking_dt_naive = datetime.strptime(bk_date_clean, "%Y-%m-%d").replace(hour=h, minute=m)
            booking_dt_mmt = booking_dt_naive.replace(tzinfo=MMT)
        except (ValueError, AttributeError):
            continue
        
        # 15 min grace period
        grace_cutoff = booking_dt_mmt + timedelta(minutes=15)
        if now_mmt <= grace_cutoff:
            continue
        
        bk_id = b.get("id")
        if not bk_id:
            continue
        
        customer_name = b.get("customerName") or b.get("memberId") or b.get("staff_name") or "Guest"
        console = b.get("consoleType") or b.get("console_id") or "Unknown"
        game = b.get("gameName") or ""
        telegram_chat_id = b.get("telegramChatId") or b.get("telegram_chat_id") or ""
        phone = b.get("phone") or ""
        
        # Re-fetch current status to avoid canceling in-progress sessions
        try:
            check = requests.get(f"{API_URL}/api/bookings/{bk_id}", headers=headers, timeout=10)
            if check.status_code == 200:
                current_status = check.json().get("booking", {}).get("status", "")
                if current_status.lower() in ("active", "done", "cancelled"):
                    print(f"  [SKIP] Booking {bk_id} status already {current_status}")
                    continue
        except Exception as e:
            print(f"  ⚠ Could not re-check status for #{bk_id}: {e}")
        
        # Cancel via API
        try:
            cancel_resp = requests.post(
                f"{API_URL}/api/bookings/cancel",
                json={"id": bk_id},
                headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                timeout=10,
            )
            cancel_data = cancel_resp.json() if cancel_resp.text else {}
        except Exception as e:
            print(f"  ✗ Failed to cancel booking {bk_id}: {e}")
            continue
        
        is_cancelled = cancel_data.get("success", False)
        
        if not is_cancelled:
            print(f"  ✗ Cancel API failed for #{bk_id}: {cancel_data}")
            continue
        
        cancelled += 1
        print(f"  ✓ Auto-cancelled #{bk_id} ({customer_name} — {bk_date_clean} {time_str})")
        
        # Notify customer
        if telegram_chat_id:
            cust_msg = (
                f"⏰ <b>Booking Auto-Cancelled</b>\n\n"
                f"သင့် booking (#{bk_id}) အတွက် အချိန်ကျော်သွားပါပြီ။\n\n"
                f"📅 {bk_date_clean}\n"
                f"⏰ {time_str}\n"
                f"🎮 {console}"
                + (f"\n🕹️ {game}" if game else "") +
                f"\n\nကျေးဇူးပြုပြီး booking အသစ် ပြန်ယူပါ။\n"
                f"ဆက်သွယ်ရန်: @psvibeofficial"
            )
            if tg_send(telegram_chat_id, cust_msg, token=CUSTOMER_BOT_TOKEN):
                notified_customers += 1
        
        # Notify staff
        if STAFF_NOTIFY_CHAT:
            staff_msg = (
                f"🚫 <b>Booking Auto-Cancelled (No-Show)</b>\n\n"
                f"Booking <b>#{bk_id}</b> — customer did not check in.\n\n"
                f"👤 {customer_name}\n"
                f"📞 {phone}\n"
                f"📅 {bk_date_clean} ⏰ {time_str}\n"
                f"🎮 {console}"
                + (f"\n🕹️ {game}" if game else "")
            )
            if tg_send(STAFF_NOTIFY_CHAT, staff_msg, token=BOT_TOKEN or CUSTOMER_BOT_TOKEN):
                notified_staff += 1
    
    print(f"Auto-cancel complete. Cancelled: {cancelled}, Customer notified: {notified_customers}, Staff notified: {notified_staff}")



def send_booking_reminders():
    """Check for confirmed/scheduled bookings starting within ~10 minutes and remind staff."""
    now_mmt = datetime.now(MMT)
    headers = {"X-API-Key": API_KEY}
    reminded_ids = set()
    
    # Load previously reminded IDs from file
    if os.path.exists(TRACK_FILE):
        try:
            with open(TRACK_FILE) as f:
                reminded_ids = set(json.load(f))
        except:
            reminded_ids = set()
    
    # Clean old entries older than 7 days
    cutoff_date = (now_mmt - timedelta(days=7)).strftime("%Y%m%d")
    reminded_ids = {x for x in reminded_ids if str(x) >= str(cutoff_date)}
    
    try:
        resp = requests.get(
            f"{API_URL}/api/bookings",
            params={},
            headers=headers,
            timeout=15,
        )
        if resp.status_code != 200:
            return
        data = resp.json()
        all_bk = []
        if isinstance(data, dict):
            inner = data.get("data", data)
            if isinstance(inner, dict):
                all_bk = inner.get("bookings", [])
            elif isinstance(inner, list):
                all_bk = inner
        elif isinstance(data, list):
            all_bk = data
        
        now_ts = now_mmt.timestamp()
        
        for b in all_bk:
            status = (b.get("status") or "").lower()
            if status not in ("confirmed",):
                continue
            
            time_slot = b.get("timeSlot") or b.get("startTime") or ""
            bk_date = b.get("date") or b.get("booking_date") or ""
            
            if not time_slot or not bk_date:
                continue
            
            # Parse booking datetime
            time_str = str(time_slot)
            if "T" in time_str:
                time_str = time_str.split("T")[1][:5]
            if " " in time_str:
                parts = time_str.split(" ")
                time_str = parts[1][:5] if len(parts) > 1 and ":" in parts[1] else parts[0][:5]
            
            try:
                h, m = map(int, time_str.split(":"))
            except:
                continue
            
            try:
                bk_date_clean = str(bk_date).split(" ")[0]
                bk_dt = datetime.strptime(bk_date_clean, "%Y-%m-%d").replace(hour=h, minute=m, tzinfo=MMT)
            except:
                continue
            
            # Is it within 8-12 minutes before start?
            mins_before = (bk_dt - now_mmt).total_seconds() / 60.0
            if not (5 <= mins_before <= 12):
                continue
            
            bk_id = b.get("id")
            if not bk_id:
                continue
            
            reminder_key = f"{now_mmt.strftime('%Y%m%d')}_{bk_id}"
            if reminder_key in reminded_ids:
                continue  # Already reminded
            
            # Send reminder to staff group
            customer = b.get("customerName") or b.get("memberId") or b.get("staff_name") or "Guest"
            phone = b.get("phone") or ""
            console = b.get("consoleType") or b.get("console_id") or "?"
            game = b.get("gameName") or ""
            duration = b.get("durationMins") or b.get("duration_mins") or ""
            
            remind_msg = (
                f"\u23F0 <b>Booking Reminder</b>\n"
                f"\u2022 <b>Booking #{bk_id}</b>\n"
                f"\uD83D\uDC64 {customer}\n"
                f"\uD83D\uDCC5 {bk_date_clean}  \uD83D\uDD50 {time_str}\n"
                f"\uD83C\uDFAE {console}  \u23F1 {duration} mins\n"
            )
            if phone:
                remind_msg += f"\U0001F4DE {phone}\n"
            if game:
                remind_msg += f"\U0001F579 {game}\n"
            remind_msg += (
                "\n"
                "\u2705 /checkin_{id} — Check In\n"
                "\u274C /cancel_{id} — Cancel Booking"
            ).format(id=bk_id)
            
            if tg_send(STAFF_NOTIFY_CHAT, remind_msg, token=BOT_TOKEN, parse_mode="HTML"):
                reminded_ids.add(reminder_key)
                print(f"  \u2713 Reminded staff about booking #{bk_id} ({customer}, {time_str})")
                # Also notify customer
                _cust_chat = b.get("telegram_chat_id") or b.get("telegramChatId") or ""
                if _cust_chat and CUSTOMER_BOT_TOKEN:
                    _cust_remind = f"\U0001F514 <b>PS VIBE Booking Reminder</b>\nBooking #{bk_id}\n\U0001F4C5 {bk_date_clean}  \U0001F550 {time_str}\n\U0001F3AE {console}  \u23F1 {duration} mins"
                    if game:
                        cust_remind += f"\n\U0001F579 {game}"
                    _cust_remind += "\n\n\u23F0 \u1014\u102d\u1029\u101b\u1031\u101b\u1000\u1039\u101b\u102e\u1019\u1031\u101c\u102c\u1031\u101b\u1019\u1039\u1019"
                    tg_send(_cust_chat, _cust_remind, token=CUSTOMER_BOT_TOKEN, parse_mode="HTML")
                    print(f"  \u2713 Reminded customer #{bk_id}")
        
        # Save reminded IDs to file
        with open(TRACK_FILE, 'w') as f:
            json.dump(list(reminded_ids), f)
    
    except Exception as e:
        print(f"Booking reminder error: {e}")



if __name__ == "__main__":
    send_booking_reminders()
    auto_cancel()
