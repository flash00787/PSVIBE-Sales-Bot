#!/usr/bin/env python3
"""PS VIBE Sales Bot — V2 Standalone Deployment Script.
This script:
1. Creates customer_bot/booking.py from V1 booking code (adapted for V2 patterns)
2. Updates customer_bot/handlers.py with aliases
3. Rewrites customer_bot/__init__.py to import from local V2 modules only
4. Rewrites customer_bot/main.py to import from local V2 modules only
5. Tests the package
6. Backs up and deletes V1
"""

import os, sys, re, subprocess, shutil
from pathlib import Path

BASE = Path('/root/psvibe_sales_bot')
V1 = BASE / 'customer_bot_original.py'
V2 = BASE / 'customer_bot'
BACKUP = Path('/root/backups')

# ── Step 1: Backup V1 ─────────────────────────────────────────────────────────
BACKUP.mkdir(parents=True, exist_ok=True)
ts = subprocess.check_output(['date', '+%Y%m%d_%H%M%S']).decode().strip()
backup_path = BACKUP / f'customer_bot_original.py.{ts}'
shutil.copy2(V1, backup_path)
print(f'✅ V1 backed up to {backup_path}')

# ── Read V1 source ────────────────────────────────────────────────────────────
v1_source = V1.read_text()

# ── Step 2: Create booking.py ─────────────────────────────────────────────────
# Extract booking/waitlist/callback/reschedule/scheduler code from V1
# Lines roughly 2500-5050 (waitlist + mybookings + refer + booking conv +
#                          scheduler + staff notify + callbacks)

# Find the boundaries
lines = v1_source.split('\n')

# We need:
# - _api_delete (sync, ~L2511)
# - waitlist handlers (~L2540-L2768)
# - cmd_mybookings, cb_mybookings_history, cmd_refer (~L2774-L2983)
# - _bk_step, _bk_intercept_menu, cmd_book, step handlers (~L2989-L4135)
# - Scheduler code: _load_sent_sets, _persist_sent_sets, etc. (~L4143-L4497)
# - _notify_staff (~L4503-L4528)
# - Callback handlers: cb_booking_action, cb_reschedule_*, cb_cancel_* (~L4534-L5040)
# - Additional handlers: cb_ai_quick, cb_game_filter (~L5042-L5186)

# Let's extract by finding function boundaries
def find_function_start(name, start_line=0):
    for i, line in enumerate(lines[start_line:], start_line+1):
        if f'def {name}(' in line or f'async def {name}(' in line:
            return i
    return None

def get_section(start_name, end_name=None):
    """Get a section from V1, from start_name function to end_name function."""
    start = find_function_start(start_name)
    if end_name:
        end = find_function_start(end_name, start)
    else:
        end = len(lines)
    return '\n'.join(lines[start-1:end-1])

# We'll build booking.py piece by piece
booking_header = '''"""
PS Vibe Customer Bot — Booking, Waitlist, Reschedule, and Callback handlers.
Adapted from customer_bot_original.py for V2 module structure.
"""
import asyncio, json, logging, os, re, time, random
from datetime import datetime, timezone, timedelta, date
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,
)
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from . import api as _api
from .handlers import (
    BK_MEMBER_CHECK, BK_MEMBER_SELECT, BK_PHONE_VERIFY, BK_DATA_CONFIRM,
    BK_NAME, BK_PHONE, BK_DATE, BK_TIME,
    BK_CONSOLE, BK_DURATION, BK_GAME, BK_CONSOLE_PREF, BK_CONFIRM,
    BK_DUP_WARN, BK_DISC_WARN, BK_CON_CONFLICT, BK_END,
    WL_PREF, WL_NAME, WL_PHONE, WL_CONFIRM,
    BTN_BOOK, BTN_STATUS, BTN_MYBOOKINGS, BTN_GAMES, BTN_HELP_BTN,
    BTN_RATE, BTN_REFRESH, BTN_CONTACT, BTN_LOCATION, BTN_PROMOTIONS,
    BTN_BALANCE, BTN_REFER, BTN_CANCEL, BTN_BACK, BTN_CONFIRM, BTN_NOT_SURE,
    BTN_BOOK_ANYWAY, BTN_BOOK_GOBACK, BTN_DISC_OK, BTN_DISC_GAME,
    BTN_DISC_TIME, BTN_CHANGE_TIME_CONFLICT,
    CONSOLE_TYPES, DURATION_OPTS, MAIN_MENU_KB,
    _step_hdr, _split_message, _bk_step, _bk_intercept_menu,
    show_main_menu,
    cmd_contact, cmd_start, cmd_myid,
)
from .data.prompts import now_mmt, today_mmt, OPEN_HOUR, CLOSE_HOUR

# ── Additional button labels (not in handlers.py) ─────────────────────────────
BTN_HAS_CARD_YES = "✅ ဟုတ်ကဲ့၊ ရှိပါတယ်"
BTN_HAS_CARD_NO  = "❌ မရှိပါ"
BTN_DATA_OK      = "✅ မှန်ပါတယ်"
BTN_NO_PREF      = "🎯 ဘာမဆို ရပါတယ်"
BTN_SWITCH_PS5   = "🎮 PS5 ပြောင်းဆော့မည်"
BTN_JOIN_WAITLIST_CONF = "📋 Waitlist ထည့်မည်"

# ── N8N booking webhook ───────────────────────────────────────────────────────
N8N_BOOKING_WEBHOOK = os.environ.get("N8N_BOOKING_WEBHOOK", "")

# ── Scheduler state ───────────────────────────────────────────────────────────
_SENT_FILE = "/tmp/psvibe_sent.json"
_reminders_sent: set = set()
_checkins_sent: set = set()
_autocancels_done: set = set()

'''

# Now let's construct booking.py by extracting the needed functions from V1

# Get ALL functions needed between _api_delete through cb_game_filter
# We'll find line numbers for each section
section_map = [
    # (start_fn, end_fn, name)
    ('_api_delete', 'wl_start', 'API_DELETE'),
    ('wl_start', 'cmd_waitlist', 'WAITLIST'),
    ('cmd_waitlist', 'cb_wl_action_end', 'WL_CMD+CB'),
    ('cmd_mybookings', 'cb_mybookings_history_end', 'MYBOOKINGS'),
    ('cmd_refer', '_bk_step', 'REFERRAL'),
    ('_bk_step', '_signal_handler', 'BOOKING_CONV'),  # big section
    ('_load_sent_sets', '_auto_cancel_booking_end', 'SCHEDULER'),
    ('_notify_staff', 'cb_booking_action_end', 'NOTIFY+CB_ACTION'),
    ('cb_reschedule_booking', 'cb_cancel_booking_confirm_end', 'RESCHEDULE'),
    ('cb_ai_quick', 'cb_game_filter_end', 'AI_QUICK+GAME_FILTER'),
]

# Simpler approach: Extract lines 2500-5200 from V1 and adapt
# Let's find the exact line numbers

# Find line numbers for key functions
func_map = {}
pattern = re.compile(r'^(async\s+)?def\s+(\w+)\s*\(.*')
for i, line in enumerate(lines, 1):
    m = pattern.match(line.strip())
    if m:
        func_map[m.group(2)] = i

print(f'Found {len(func_map)} functions in V1')

# The key ranges we need:
# 1. _api_delete (sync version) - ~L2511
# 2. Waitlist: wl_start → end of cb_wl_action (~L2540-L2769)
# 3. My Bookings + History: cmd_mybookings → end of cb_mybookings_history (~L2774-L2935)
# 4. Referral: cmd_refer → line before _bk_step (~L2937-L2984)
# 5. Entire booking conversation: _bk_step → end of cmd_cancel (~L2989-L4135)
# 6. Scheduler: _load_sent_sets → end of _auto_cancel_booking (~L4143-L4497)
# 7. Staff notify: _notify_staff (~L4503-L4528)  
# 8. Booking actions callback: cb_booking_action (~L4534-L4708)
# 9. Reschedule callbacks: cb_reschedule_booking → end of cb_reschedule_cancel (~L4714-L4959)
# 10. Cancel callbacks: cb_cancel_booking → end of cb_cancel_booking_confirm (~L4963-L5036)
# 11. AI Quick + Game Filter: cb_ai_quick → end of cb_game_filter (~L5042-L5186)

BOOKING_SOURCE_LINES = []
for start_line, end_line in [
    (2511, 2521),   # _api_delete
    (2540, 2770),   # waitlist + cb_wl_action
    (2774, 2936),   # mybookings + history
    (2937, 2985),   # referral  
    (2989, 4136),   # booking conversation
    (4143, 4498),   # scheduler
    (4503, 4529),   # notify_staff
    (4534, 4709),   # cb_booking_action
    (4714, 4960),   # reschedule callbacks
    (4963, 5037),   # cancel callbacks
    (5042, 5187),   # AI Quick + Game Filter
]:
    BOOKING_SOURCE_LINES.extend(range(start_line, end_line + 1))

# Extract the code
booking_code_lines = []
for i in sorted(set(BOOKING_SOURCE_LINES)):
    if 1 <= i <= len(lines):
        booking_code_lines.append(lines[i-1])

booking_source = '\n'.join(booking_code_lines)

# Now adapt the code for V2 patterns:
# 1. Replace `asyncio.to_thread(_api_get, ...)` → `_api._api_get(...)`
# 2. Replace `asyncio.to_thread(_api_post, ...)` → `_api._api_post(...)`
# 3. Replace `asyncio.to_thread(_api_patch, ...)` → `_api._api_patch(...)`
# 4. Replace `asyncio.to_thread(_api_delete, ...)` → `_api._api_delete(...)`
# 5. Replace `asyncio.to_thread(_tg_send, ...)` → `_api._tg_send(...)`
# 6. Replace `asyncio.to_thread(_fetch_games, ...)` → `_api._fetch_games(...)`
# 7. Replace `asyncio.to_thread(_fetch_members)` → `_api._fetch_members()`
# 8. Replace `asyncio.to_thread(_fetch_consoles)` → `_api._fetch_consoles()`
# 9. Replace `asyncio.to_thread(_fetch_config)` → `_api._fetch_config()`
# 10. Replace `asyncio.to_thread(_fetch_contacts)` → `_api._fetch_contacts()`
# 11. Replace `asyncio.to_thread(_fetch_promotions)` → `_api._fetch_promotions()`
# 12. Replace `asyncio.to_thread(_fetch_games_full)` → `_api._fetch_games_full()`
# 13. Replace `_cache_get(` → `await _api._cache_get(`
# 14. Replace `_cache_set(` → `await _api._cache_set(`
# 15. Replace `_cache_pop(` → `await _api._cache_pop(`
# 16. Replace `asyncio.to_thread(track_usage,` → `_api.track_usage(`
# 17. Replace `asyncio.to_thread(_contact_mention)` → `_api._contact_mention()`
# 18. Replace `_build_rate_lines()` → `await _api._build_rate_lines()`
# 19. Replace `asyncio.to_thread(_build_rate_lines)` → `_api._build_rate_lines()`
# 20. Handle `log_to_sheet` → `_api.log_to_sheet`

# Complex patterns first (multi-line may need care)
# Do string replacements
adapted = booking_source

# Replacements (order matters - longer patterns first)
replacements = [
    # Function calls via asyncio.to_thread
    (r'await asyncio\.to_thread\(_api_get,\s*', 'await _api._api_get('),
    (r'asyncio\.to_thread\(_api_get,\s*', '_api._api_get('),
    (r'await asyncio\.to_thread\(_api_post,\s*', 'await _api._api_post('),
    (r'asyncio\.to_thread\(_api_post,\s*', '_api._api_post('),
    (r'await asyncio\.to_thread\(_api_patch,\s*', 'await _api._api_patch('),
    (r'asyncio\.to_thread\(_api_patch,\s*', '_api._api_patch('),
    (r'await asyncio\.to_thread\(_api_delete,\s*', 'await _api._api_delete('),
    (r'asyncio\.to_thread\(_api_delete,\s*', '_api._api_delete('),
    (r'await asyncio\.to_thread\(_tg_send,\s*', 'await _api._tg_send('),
    (r'asyncio\.to_thread\(_tg_send,\s*', '_api._tg_send('),
    (r'await asyncio\.to_thread\(_contact_mention\)', 'await _api._contact_mention()'),
    (r'asyncio\.to_thread\(_contact_mention\)', '_api._contact_mention()'),
    
    # Cached fetchers
    (r'await asyncio\.to_thread\(_fetch_games,\s*', 'await _api._fetch_games('),
    (r'asyncio\.to_thread\(_fetch_games,\s*', '_api._fetch_games('),
    (r'await asyncio\.to_thread\(_fetch_games_full\)', 'await _api._fetch_games_full()'),
    (r'asyncio\.to_thread\(_fetch_games_full\)', '_api._fetch_games_full()'),
    (r'await asyncio\.to_thread\(_fetch_members\)', 'await _api._fetch_members()'),
    (r'asyncio\.to_thread\(_fetch_members\)', '_api._fetch_members()'),
    (r'await asyncio\.to_thread\(_fetch_consoles\)', 'await _api._fetch_consoles()'),
    (r'asyncio\.to_thread\(_fetch_consoles\)', '_api._fetch_consoles()'),
    (r'await asyncio\.to_thread\(_fetch_config\)', 'await _api._fetch_config()'),
    (r'asyncio\.to_thread\(_fetch_config\)', '_api._fetch_config()'),
    (r'await asyncio\.to_thread\(_fetch_contacts\)', 'await _api._fetch_contacts()'),
    (r'asyncio\.to_thread\(_fetch_contacts\)', '_api._fetch_contacts()'),
    (r'await asyncio\.to_thread\(_fetch_promotions\)', 'await _api._fetch_promotions()'),
    (r'asyncio\.to_thread\(_fetch_promotions\)', '_api._fetch_promotions()'),
    (r'await asyncio\.to_thread\(_fetch_sales_data\)', 'await _api._fetch_sales_data()'),
    (r'asyncio\.to_thread\(_fetch_sales_data\)', '_api._fetch_sales_data()'),
    
    # Cache functions
    (r'await asyncio\.to_thread\(_cache_get,\s*', 'await _api._cache_get('),
    (r'asyncio\.to_thread\(_cache_get,\s*', '_api._cache_get('),
    (r'await asyncio\.to_thread\(_cache_pop,\s*', 'await _api._cache_pop('),
    (r'asyncio\.to_thread\(_cache_pop,\s*', '_api._cache_pop('),
    
    # Direct cache usage (these were global functions in V1, now in api)
    # Keep _cache_get, _cache_set, _cache_pop as local fallbacks
    (r'= _cache_get\(', '= await _api._cache_get('),
    (r'= _cache_pop\(', '= await _api._cache_pop('),
    
    # track_usage
    (r'asyncio\.create_task\(track_usage\(', 'asyncio.create_task(_api.track_usage('),
    (r'await asyncio\.to_thread\(track_usage,\s*', 'await _api.track_usage('),
    
    # log_to_sheet
    (r'asyncio\.create_task\(log_to_sheet\(', 'asyncio.create_task(_api.log_to_sheet('),
    (r'await asyncio\.to_thread\(log_to_sheet,\s*', 'await _api.log_to_sheet('),
    
    # build_rate_lines
    (r'await asyncio\.to_thread\(_build_rate_lines\)', 'await _api._build_rate_lines()'),
    
    # check_disc_conflict
    (r'await asyncio\.to_thread\(_check_disc_conflict_sync,\s*', 'await _api._check_disc_conflict_sync('),
    
    # _post_n8n_booking
    (r'await asyncio\.to_thread\(_post_n8n_booking,\s*', 'await _post_n8n_booking('),
    
    # _notify_staff → local copy
    # _format_promotion → use handlers version
]

for pattern, replacement in replacements:
    adapted = re.sub(pattern, replacement, adapted)

# Remove the duplicate function definitions that are now imported
# Remove _api_delete sync function (we'll use api._api_delete)
adapted = re.sub(
    r'def _api_delete\(path: str\):.*?(?=\n\n(?:async )?def )',
    '# _api_delete is now in api.py\n',
    adapted, flags=re.DOTALL
)

# Remove GAME_LIBRARY, _is_real_game, _build_live_game_library_text if present 
# (they're in data/games.py)

# Now write booking.py
booking_full = booking_header + '\n' + adapted

# Add _post_n8n_booking function if not in adapted
if '_post_n8n_booking' not in booking_full:
    booking_full += '''
# ── N8N Booking Webhook ────────────────────────────────────────────────────────
def _post_n8n_booking(bk_id: int, payload: dict, tg_chat: str = "") -> bool:
    """POST booking info to n8n for restart-proof reminder scheduling."""
    if not N8N_BOOKING_WEBHOOK:
        return False
    import re as _re, urllib.request as _req
    date_str  = payload.get("date", "")
    time_slot = payload.get("timeSlot", "")
    m1 = _re.match(r"(\d+)/(\d+)/(\d+)", date_str or "")
    m2 = _re.match(r"(\d{4})-(\d{2})-(\d{2})", date_str or "")
    if not (m1 or m2) or not time_slot:
        return False
    try:
        if m1:
            mon, day, year = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
        else:
            year, mon, day = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
        h, mi = map(int, time_slot.split(":"))
        from datetime import datetime as _dt, timezone as _tz, timedelta as _td
        MMT = _tz(_td(hours=6, minutes=30))
        booking_dt  = _dt(year, mon, day, h, mi, tzinfo=MMT)
        booking_iso = booking_dt.isoformat()
    except Exception as e:
        logging.warning("_post_n8n_booking parse error: %s", e)
        return False
    body = json.dumps({
        "bk_id":            bk_id,
        "customer_name":    payload.get("customerName", ""),
        "phone":            payload.get("phone", ""),
        "console_id":       payload.get("consoleId") or "",
        "console_type":     payload.get("consoleType", ""),
        "date":             date_str,
        "time_slot":        time_slot,
        "booking_iso":      booking_iso,
        "duration_mins":    payload.get("durationMins", 60),
        "staff_notify_chat": _api.STAFF_NOTIFY_CHAT,
        "telegram_chat_id": tg_chat,
        "replit_api_url":   _api.API_BASE,
    }).encode()
    try:
        r = _req.Request(N8N_BOOKING_WEBHOOK, data=body,
                         headers={"Content-Type": "application/json"}, method="POST")
        with _req.urlopen(r, timeout=10) as resp:
            _ = resp.read()
        logging.info("n8n booking reminder queued — bk#%s at %s", bk_id, booking_iso)
        return True
    except Exception as e:
        logging.warning("n8n booking webhook POST failed: %s", e)
        return False
'''

# Add the BK_END constant reference
booking_full += '\nBK_END = ConversationHandler.END\n'

booking_path = V2 / 'booking.py'
booking_path.write_text(booking_full)
print(f'✅ Created {booking_path} ({len(booking_full)} bytes)')

# ── Step 3: Add aliases to handlers.py ───────────────────────────────────────
handlers_path = V2 / 'handlers.py'
handlers_src = handlers_path.read_text()

# Add aliases right after the last async function or at the end before imports
aliases = '''
# ── Aliases for main.py compatibility ────────────────────────────────────────
start = cmd_start
refresh_cmd = cmd_refresh
menu_cmd = cmd_menu
today_cmd = cmd_today
rate_cmd = cmd_rate
myid_cmd = cmd_myid
contact_cmd = cmd_contact
promotions_cmd = cmd_promotions
feedback_cmd = cmd_feedback
handle_free_text = handle_menu_buttons
bk_start = cmd_book
bk_end = cmd_cancel

# Re-export booking handlers from booking module
from .booking import (
    step_bk_member_check as bk_member_check,
    step_bk_member_select as bk_member_select,
    step_bk_phone_verify as bk_phone_verify,
    step_bk_data_confirm as bk_data_confirm,
    step_bk_name as bk_name,
    step_bk_phone as bk_phone,
    step_bk_date as bk_date,
    step_bk_time as bk_time,
    step_bk_console as bk_console,
    step_bk_duration as bk_duration,
    step_bk_game as bk_game,
    step_bk_console_pref as bk_console_pref,
    step_bk_confirm as bk_confirm,
    step_bk_dup_warn as bk_disc_warn,
    step_bk_con_conflict,
    step_bk_disc_warn,
    cb_booking_action,
    cb_mybookings_history,
    cb_reschedule_booking,
    cb_reschedule_date,
    cb_reschedule_time,
    cb_reschedule_custom_time_prompt,
    cb_reschedule_confirm,
    cb_reschedule_cancel,
    cb_cancel_booking,
    cb_cancel_booking_confirm,
    cb_wl_action,
)
'''

# Insert aliases before the last import (before 'from .booking import')
# Actually just append to end
if 'start = cmd_start' not in handlers_src:
    handlers_src += aliases
    handlers_path.write_text(handlers_src)
    print('✅ Added aliases to handlers.py')

# ── Step 4: Fix __init__.py ──────────────────────────────────────────────────
init_path = V2 / '__init__.py'
init_content = '''"""PS VIBE Customer Bot — refactored package."""
from .handlers import (
    start, refresh_cmd, menu_cmd, today_cmd, rate_cmd, myid_cmd,
    contact_cmd, promotions_cmd, feedback_cmd,
    handle_menu_buttons, handle_free_text,
    bk_start, bk_member_check, bk_member_select, bk_phone_verify,
    bk_data_confirm, bk_name, bk_phone, bk_date,
    bk_time, bk_console, bk_duration, bk_game, bk_console_pref,
    bk_confirm, bk_end,
    cb_booking_action, cb_mybookings_history,
    cb_reschedule_booking, cb_reschedule_date, cb_reschedule_time,
    cb_reschedule_custom_time_prompt, cb_reschedule_confirm,
    cb_reschedule_cancel, cb_cancel_booking, cb_cancel_booking_confirm,
    cb_wl_action,
    BK_MEMBER_CHECK, BK_MEMBER_SELECT, BK_PHONE_VERIFY, BK_DATA_CONFIRM,
    BK_NAME, BK_PHONE, BK_DATE, BK_TIME,
    BK_CONSOLE, BK_DURATION, BK_GAME, BK_CONSOLE_PREF, BK_CONFIRM,
    BK_DUP_WARN, BK_DISC_WARN, BK_CON_CONFLICT, BK_END,
    WL_PREF, WL_NAME, WL_PHONE, WL_CONFIRM,
    MAIN_MENU_KB, CONSOLE_TYPES, DURATION_OPTS,
    show_main_menu,
)

__all__ = [
    'start', 'refresh_cmd', 'menu_cmd', 'today_cmd', 'rate_cmd', 'myid_cmd',
    'contact_cmd', 'promotions_cmd', 'feedback_cmd',
    'handle_menu_buttons', 'handle_free_text',
    'bk_start', 'bk_member_check', 'bk_member_select', 'bk_phone_verify',
    'bk_data_confirm', 'bk_name', 'bk_phone', 'bk_date',
    'bk_time', 'bk_console', 'bk_duration', 'bk_game', 'bk_console_pref',
    'bk_confirm', 'bk_end',
    'cb_booking_action', 'cb_mybookings_history',
    'cb_reschedule_booking', 'cb_reschedule_date', 'cb_reschedule_time',
    'cb_reschedule_custom_time_prompt', 'cb_reschedule_confirm',
    'cb_reschedule_cancel', 'cb_cancel_booking', 'cb_cancel_booking_confirm',
    'cb_wl_action',
    'BK_MEMBER_CHECK', 'BK_MEMBER_SELECT', 'BK_PHONE_VERIFY', 'BK_DATA_CONFIRM',
    'BK_NAME', 'BK_PHONE', 'BK_DATE', 'BK_TIME',
    'BK_CONSOLE', 'BK_DURATION', 'BK_GAME', 'BK_CONSOLE_PREF', 'BK_CONFIRM',
    'BK_DUP_WARN', 'BK_DISC_WARN', 'BK_CON_CONFLICT', 'BK_END',
    'WL_PREF', 'WL_NAME', 'WL_PHONE', 'WL_CONFIRM',
    'MAIN_MENU_KB', 'CONSOLE_TYPES', 'DURATION_OPTS',
    'show_main_menu',
]
'''
init_path.write_text(init_content)
print('✅ Rewrote __init__.py')

# ── Step 5: Fix main.py ─────────────────────────────────────────────────────
main_path = V2 / 'main.py'
main_content = '''"""PS VIBE Customer Bot (Refactored v3) — Entry Point."""
import sys, os, asyncio, logging, time
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, ConversationHandler,
    MessageHandler, filters, CallbackQueryHandler,
)
from .handlers import (
    start, refresh_cmd, menu_cmd, today_cmd, rate_cmd, myid_cmd,
    contact_cmd, promotions_cmd, feedback_cmd,
    handle_menu_buttons, handle_free_text,
    bk_start, bk_member_check, bk_member_select, bk_phone_verify,
    bk_data_confirm, bk_name, bk_phone, bk_date,
    bk_time, bk_console, bk_duration, bk_game, bk_console_pref,
    bk_confirm, bk_end,
    cb_booking_action, cb_mybookings_history,
    cb_reschedule_booking, cb_reschedule_date, cb_reschedule_time,
    cb_reschedule_custom_time_prompt, cb_reschedule_confirm,
    cb_reschedule_cancel, cb_cancel_booking, cb_cancel_booking_confirm,
    cb_wl_action,
    BK_MEMBER_CHECK, BK_MEMBER_SELECT, BK_PHONE_VERIFY, BK_DATA_CONFIRM,
    BK_NAME, BK_PHONE, BK_DATE, BK_TIME,
    BK_CONSOLE, BK_DURATION, BK_GAME, BK_CONSOLE_PREF, BK_CONFIRM,
    BK_DUP_WARN, BK_DISC_WARN, BK_CON_CONFLICT, BK_END,
)
from .api import _CACHE_TTL as _orig_cache_ttl

_log = logging.getLogger(__name__)
BOT_TOKEN = os.environ.get('CUSTOMER_BOT_TOKEN', '')
CACHE_TTL_GAMES = int(os.environ.get('CACHE_TTL_GAMES', '300'))
CACHE_TTL_MEMBERS = int(os.environ.get('CACHE_TTL_MEMBERS', '300'))
CACHE_TTL_CONSOLES = int(os.environ.get('CACHE_TTL_CONSOLES', '300'))
CACHE_TTL_CONTACTS = int(os.environ.get('CACHE_TTL_CONTACTS', '600'))
CACHE_TTL_CONFIG = int(os.environ.get('CACHE_TTL_CONFIG', '300'))
CACHE_TTL_PROMOTIONS = int(os.environ.get('CACHE_TTL_PROMOTIONS', '1800'))

def _register_handlers(app):
    """Register all command, conversation, and callback handlers on the Application."""
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('refresh', refresh_cmd))
    app.add_handler(CommandHandler('menu', menu_cmd))
    app.add_handler(CommandHandler('today', today_cmd))
    app.add_handler(CommandHandler('rate', rate_cmd))
    app.add_handler(CommandHandler('myid', myid_cmd))
    app.add_handler(CommandHandler('contact', contact_cmd))
    app.add_handler(CommandHandler('promotions', promotions_cmd))
    app.add_handler(CommandHandler('feedback', feedback_cmd))
    
    bk_conv = ConversationHandler(
        entry_points=[
            CommandHandler('book', bk_start),
            CommandHandler('booking', bk_start),
            MessageHandler(filters.Regex(r'^\\U0001f3ae\\s*\\u101d\\u1004\\u1039\\u1019\\u103a\\u101c\\u1031|\\U0001f3ae\\s*Book'), bk_start),
        ],
        states={
            BK_MEMBER_CHECK: [CallbackQueryHandler(bk_member_check, pattern=r'^bk_mem:(yes|no|existing)$')],
            BK_MEMBER_SELECT: [CallbackQueryHandler(bk_member_select, pattern=r'^bk_sel:\\d+$')],
            BK_PHONE_VERIFY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_phone_verify)],
            BK_DATA_CONFIRM: [CallbackQueryHandler(bk_data_confirm, pattern=r'^bk_dc:(yes|no|edit)$')],
            BK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_name)],
            BK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_phone)],
            BK_DATE: [CallbackQueryHandler(bk_date, pattern=r'^bkdate:')],
            BK_TIME: [CallbackQueryHandler(bk_time, pattern=r'^(bktime:|bk_custom:)')],
            BK_CONSOLE: [CallbackQueryHandler(bk_console, pattern=r'^bk_con:')],
            BK_DURATION: [CallbackQueryHandler(bk_duration, pattern=r'^bk_dur:')],
            BK_GAME: [CallbackQueryHandler(bk_game, pattern=r'^bk_game:')],
            BK_CONSOLE_PREF: [CallbackQueryHandler(bk_console_pref, pattern=r'^bk_cp:')],
            BK_CONFIRM: [CallbackQueryHandler(bk_confirm, pattern=r'^bk_ok:')],
            BK_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_end)],
        },
        fallbacks=[CommandHandler('cancel', bk_end)],
    )
    app.add_handler(bk_conv)
    
    app.add_handler(CallbackQueryHandler(cb_booking_action, pattern=r'^bk:(approve|reject|arrived|noshow):\\d+$'))
    app.add_handler(CallbackQueryHandler(cb_mybookings_history, pattern=r'^mybk:history$'))
    app.add_handler(CallbackQueryHandler(cb_reschedule_booking, pattern=r'^bkr:\\d+$'))
    app.add_handler(CallbackQueryHandler(cb_reschedule_date, pattern=r'^rsd:\\d+:[\\d-]+$'))
    app.add_handler(CallbackQueryHandler(cb_reschedule_time, pattern=r'^rst:\\d+:[\\d-]+:\\d{2}:\\d{2}$'))
    app.add_handler(CallbackQueryHandler(cb_reschedule_custom_time_prompt, pattern=r'^rscustom:\\d+:[\\d-]+$'))
    app.add_handler(CallbackQueryHandler(cb_reschedule_confirm, pattern=r'^rsok:\\d+:[\\d-]+:\\d{2}:\\d{2}$'))
    app.add_handler(CallbackQueryHandler(cb_reschedule_cancel, pattern=r'^rscancel:\\d+$'))
    app.add_handler(CallbackQueryHandler(cb_cancel_booking, pattern=r'^bkc:\\d+$'))
    app.add_handler(CallbackQueryHandler(cb_cancel_booking_confirm, pattern=r'^cx(ok|no):\\d+$'))
    app.add_handler(CallbackQueryHandler(cb_wl_action, pattern=r'^wl:(check|cancel:\\d+)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_free_text), group=1)

async def error_handler(update, context):
    """Log unhandled errors and notify the user with a friendly message."""
    _log.error('Unhandled error: %s', context.error, exc_info=context.error)
    try:
        if update and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='\\u26a0\\ufe0f \\u1004\\u1014\\u1039\\u1000\\u1039\\u1018\\u102c\\u1001\\u103b\\u102d\\u102f\\u1004\\u1039\\u1001\\u103b\\u102d\\u1031\\u102c\\u1004\\u103a\\u1000\\u1039\\u101b\\u103e\\u1004\\u1039\\u101e\\u1031\\u101c\\u102c\\u1012\\u1039 \\u1018\\u1031\\u102c\\u1004\\u103a \\u101e\\u1001\\u1039\\u1001\\u103e\\u102c\\u1014\\u1039 \\u1005\\u102c\\u1019\\u1031\\u102c\\u1000\\u1039 \\u1019\\u103b\\u102c\\u1014\\u1039\\u1001\\u103d\\u102c\\u101c\\u1039 \\u1018\\u103c\\u1014\\u1039\\u1000\\u1039 \\u1000\\u103c\\u102d\\u1033\\u1018\\u1039 \\u1000\\u103c\\u102d\\u1033\\u101b\\u103d\\u1000\\u1039\\u1000\\u102d\\u102f\\u101b\\u1039\\u1019\\u102d\\u1000\\u1039\\u1019\\u103b\\u102c\\u1015\\u1031\\u101b\\u103e\\u1000\\u1039 \\u101e\\u100a\\u1039 \\u1000\\u103c\\u102d\\u1033\\u101b\\u1039\\u1019\\u103e\\u100a\\u1039 \\u1019\\u103b\\u102c\\u1014\\u1039\\u1001\\u103d\\u102c\\u101c\\u1039\\u1019\\u103b\\u102c \\u1005\\u1031\\u102c\\u1004\\u1039\\u1000\\u103c\\u1032\\u1000\\u103d\\u1031\\u101b\\u1039\\u1000\\u103c\\u1032\\u1000\\u103d\\u1031\\u101b\\u1039\\u1014\\u103d\\u1031 \\u101e\\u101c\\u102c\\u1004\\u1039 \\u101e\\u102d\\u102f\\u1021\\u1031\\u102c\\u1000\\u1039 \\u1006\\u102f\\u1015\\u1039\\u1000\\u103b\\u102c\\u101c\\u1039 \\u1000\\u103c\\u102d\\u1033\\u101b\\u1039\\u1014\\u103d\\u1031\\u1015\\u1032 \\u1018\\u1031\\u101c \\u101e\\u1031\\u102c\\u1004\\u1039\\u1000\\u103c\\u1032\\u1000\\u103d\\u1031\\u101b\\u1039\\u1000\\u103c\\u1032\\u1000\\u103d\\u1031\\u101b\\u1039\\u1014\\u103d\\u1031\\u1014\\u103d\\u1031\\u1014\\u103d\\u1031',
            )
    except Exception:
        pass

async def _post_init(app):
    """Start background tasks after app initialization."""
    from .api import _cache_sweeper
    asyncio.create_task(_cache_sweeper())
    _log.info('Cache sweeper started')


def main():
    """Build and run the Customer Bot polling application.

    Configures cache TTLs, wires all handlers, and starts long-polling.
    Does nothing if CUSTOMER_BOT_TOKEN is not set.
    """
    if not BOT_TOKEN:
        _log.error('CUSTOMER_BOT_TOKEN not set')
        return
    
    from . import api
    api._CACHE_TTL = {
        'games': CACHE_TTL_GAMES, 'members': CACHE_TTL_MEMBERS,
        'consoles': CACHE_TTL_CONSOLES, 'contacts': CACHE_TTL_CONTACTS,
        'config': CACHE_TTL_CONFIG, 'promotions': CACHE_TTL_PROMOTIONS,
    }
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_error_handler(error_handler)
    app.post_init = _post_init
    _register_handlers(app)
    
    _log.info('Customer bot (refactored v3) starting polling...')
    app.run_polling(drop_pending_updates=True)

def run():
    """Forever loop: start main() and auto-restart on crash with a 5-second backoff."""
    while True:
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            main()
        except KeyboardInterrupt:
            break
        except Exception as exc:
            _log.error('Crash: %s — restart 5s', exc, exc_info=True)
            time.sleep(5)

if __name__ == '__main__':
    run()
'''
main_path.write_text(main_content)
print('✅ Rewrote main.py')

# ── Step 6: Test V2 import ──────────────────────────────────────────────────
print('\n📋 Testing V2 import...')
result = subprocess.run(
    [sys.executable, '-c', 
     "import sys; sys.path.insert(0, '/root/psvibe_sales_bot'); "
     "from customer_bot import *; print('V2 import OK')"],
    capture_output=True, text=True, timeout=30
)
if result.returncode == 0 and 'V2 import OK' in result.stdout:
    print('✅ V2 import test PASSED')
else:
    print(f'❌ V2 import test FAILED:\nstdout: {result.stdout}\nstderr: {result.stderr}')
    # Try to get more details
    result2 = subprocess.run(
        [sys.executable, '-c', 
         "import sys; sys.path.insert(0, '/root/psvibe_sales_bot'); "
         "import customer_bot; print('basic import OK')"],
        capture_output=True, text=True, timeout=30
    )
    print(f'Basic import: {result2.stdout}\n{result2.stderr}')

# ── Step 7: Check syntax ────────────────────────────────────────────────────
print('\n📋 Checking syntax...')
for pyfile in [V2 / 'booking.py', V2 / 'main.py', V2 / '__init__.py', V2 / 'handlers.py']:
    result = subprocess.run(
        [sys.executable, '-m', 'py_compile', str(pyfile)],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode == 0:
        print(f'  ✅ {pyfile.name} — syntax OK')
    else:
        print(f'  ❌ {pyfile.name} — SYNTAX ERROR:\n{result.stderr}')

print('\n✅ Deployment preparation complete!')
print(f'Backup: {backup_path}')
