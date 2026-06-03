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
    
    for status_filter in ("confirmed", "pending", "scheduled"):
        try:
            resp = requests.get(
                f"{API_URL}/api/bookings/search",
                params={"status": status_filter, "api_key": API_KEY},
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
        if status not in ("confirmed", "pending", "scheduled"):
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
        
        # Cancel via API
        try:
            cancel_resp = requests.post(
                f"{API_URL}/api/bookings/cancel",
                params={"api_key": API_KEY},
                json={"id": bk_id},
                headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                timeout=10,
            )
            cancel_data = cancel_resp.json() if cancel_resp.text else {}
        except Exception as e:
            print(f"  ✗ Failed to cancel booking {bk_id}: {e}")
            continue
        
        is_cancelled = (
            cancel_data.get("success") or
            (isinstance(cancel_data.get("data"), dict) and cancel_data["data"].get("message"))
        )
        
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


if __name__ == "__main__":
    auto_cancel()
