const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();

conn.on('ready', () => {
  // First, read the current booking.py to get exact content
  conn.exec('cat /root/psvibe-sales-bot/customer_bot/booking.py', (err, stream) => {
    let data = '';
    stream.on('data', c => data += c);
    stream.on('close', () => {
      // Apply fixes using sed/python on remote
      const fixCmd = `python3 << 'PYEOF'
import re

with open("/root/psvibe-sales-bot/customer_bot/booking.py", "r") as f:
    content = f.read()

# ── FIX 1: _format_booking_line — better console display + robust field access ──
old = '''    bk_id = b.get("id", "?")
    status = str(b.get("status", "")).lower()
    date = b.get("booking_date", b.get("date", "?"))
    time_str = b.get("booking_time", b.get("timeSlot", b.get("startTime", "?")))
    if "T" in str(time_str):
        time_str = str(time_str).split("T")[1][:5]
    console_type = b.get("console_id", b.get("consoleType", "?"))
    duration = b.get("duration_mins", b.get("durationMins", ""))
    game = b.get("game_name", b.get("gameName", ""))
    phone = b.get("phone", "")'''

new = '''    bk_id = b.get("id", "?")
    status = str(b.get("status", "")).lower()
    date = b.get("booking_date") or b.get("date") or "?"
    time_str = b.get("booking_time") or b.get("timeSlot") or b.get("startTime") or "?"
    if "T" in str(time_str):
        time_str = str(time_str).split("T")[1][:5]
    # For pending bookings, console_id may store the type (e.g. "PS5", "PS5 Pro")
    # For confirmed bookings, console_id is the specific console (e.g. "C - 01")
    # Prefer consoleType (user-friendly), fall back to console_id, "PS5" default
    raw_console = b.get("consoleType") or b.get("console_id") or ""
    if not str(raw_console).strip():
        raw_console = "PS5"
    console_type = str(raw_console)
    duration = b.get("duration_mins") or b.get("durationMins") or ""
    game = b.get("game_name") or b.get("gameName") or ""
    phone = b.get("phone") or ""'''

if old in content:
    content = content.replace(old, new)
    print("FIX 1 APPLIED: _format_booking_line")
else:
    print("FIX 1 SKIPPED: pattern not found (may already be fixed)")

# ── FIX 2: _parse_booking_datetime_mmt — handle datetime objects ──
old2 = '''    bk_date = booking.get("date") or booking.get("booking_date") or ""
    time_slot = booking.get("timeSlot") or booking.get("startTime") or ""
    
    if not bk_date or not time_slot:
        return None
    
    # Clean date (remove time part if present)
    bk_date_clean = str(bk_date).split(" ")[0]'''

new2 = '''    bk_date = booking.get("date") or booking.get("booking_date") or ""
    time_slot = booking.get("timeSlot") or booking.get("startTime") or ""
    
    if not bk_date or not time_slot:
        return None
    
    # Clean date: handle datetime/date objects as well as strings
    if hasattr(bk_date, "strftime"):
        bk_date_clean = bk_date.strftime("%Y-%m-%d")
    else:
        bk_date_str = str(bk_date)
        bk_date_clean = bk_date_str.split(" ")[0]'''

if old2 in content:
    content = content.replace(old2, new2)
    print("FIX 2 APPLIED: _parse_booking_datetime_mmt")
else:
    print("FIX 2 SKIPPED: pattern not found")

# ── FIX 3: cmd_cancel_booking — use correct API endpoint ──
# The existing code uses _api_patch which should work with patch_routes.py endpoint
# But let's verify and add robustness
old3 = '''    try:
        result = await _api._api_patch(f"bookings/{bk_id}/status", {
            "status": "cancelled",
            "staff_note": "Cancelled by customer",
        })'''

new3 = '''    try:
        result = await _api._api_patch(f"bookings/{bk_id}/status", {
            "status": "cancelled",
            "staff_note": "Cancelled by customer",
        })'''

# No change needed here - the endpoint exists in patch_routes.py
# But let's add better error handling
old3b = '''        if result and isinstance(result, dict) and result.get("success"):
            await update.message.reply_text(
                f"✅ *Booking #{bk_id} ကို ပယ်ဖျက်လိုက်ပါပြီ။*"
            )
        else:
            err = result.get("error", "") if isinstance(result, dict) else ""
            await update.message.reply_text(
                f"❌ Booking #{bk_id} ကို ပယ်ဖျက်မရပါ။ {err}",
            )'''

new3b = '''        if result and isinstance(result, dict) and (result.get("success") or result.get("status") == "cancelled"):
            await update.message.reply_text(
                f"✅ *Booking #{bk_id} ကို ပယ်ဖျက်လိုက်ပါပြီ။*"
            )
        else:
            err = (result or {}).get("error", "") if isinstance(result, dict) else ""
            await update.message.reply_text(
                f"❌ Booking #{bk_id} ကို ပယ်ဖျက်မရပါ။ {err}",
            )'''

if old3b in content:
    content = content.replace(old3b, new3b)
    print("FIX 3 APPLIED: cmd_cancel_booking error handling")
else:
    print("FIX 3 SKIPPED: pattern not found")

# ── FIX 4: Add NO_BOOKINGS_MSG import/fix the trailing comma issue ──
# The trailing comma after reply_text is fine in Python, but let's check
# for parse_mode issues in cmd_cancel_booking
old4 = '''            await update.message.reply_text(
                f"✅ *Booking #{bk_id} ကို ပယ်ဖျက်လိုက်ပါပြီ။*"
            )'''

new4 = '''            await update.message.reply_text(
                f"✅ *Booking #{bk_id} ကို ပယ်ဖျက်လိုက်ပါပြီ။*",
                parse_mode="Markdown",
            )'''

if old4 in content:
    content = content.replace(old4, new4)
    print("FIX 4 APPLIED: parse_mode for cancel message")
else:
    print("FIX 4 SKIPPED: pattern not found")

# Write back
with open("/root/psvibe-sales-bot/customer_bot/booking.py", "w") as f:
    f.write(content)

# Verify
import subprocess
r = subprocess.run(["python3", "-m", "py_compile", "/root/psvibe-sales-bot/customer_bot/booking.py"],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("VERIFY: py_compile PASS")
else:
    print("VERIFY: py_compile FAIL")
    print(r.stderr[:500])

print("DONE")
PYEOF`;

      conn.exec(fixCmd, (err2, stream2) => {
        let out = '';
        stream2.on('data', c => out += c);
        stream2.stderr.on('data', c => out += c);
        stream2.on('close', () => {
          console.log('FIX OUTPUT:\n' + out);
          
          // Verify the fix
          conn.exec('python3 -m py_compile /root/psvibe-sales-bot/customer_bot/booking.py && echo "SYNTAX: OK" || echo "SYNTAX: FAIL"', (err3, stream3) => {
            let out3 = '';
            stream3.on('data', c => out3 += c);
            stream3.on('close', () => {
              console.log('SYNTAX CHECK: ' + out3.trim());
              
              // Show the fixed function
              conn.exec('grep -A 20 "def _format_booking_line" /root/psvibe-sales-bot/customer_bot/booking.py', (err4, stream4) => {
                let out4 = '';
                stream4.on('data', c => out4 += c);
                stream4.on('close', () => {
                  console.log('\n=== FIXED _format_booking_line ===\n' + out4);
                  conn.end();
                });
              });
            });
          });
        });
      });
    });
  });
});

conn.on('error', (err) => { console.error('SSH ERROR:', err.message); process.exit(1); });
conn.connect({host:'5.223.81.16',port:22,username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),readyTimeout:15000});
