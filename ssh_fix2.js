const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();

conn.on('ready', () => {
  const fixCmd = `python3 << 'PYEOF'
import re

# ── FIX 5: booking.py — switch back to console_id first (not consoleType which is hardcoded in app.py) ──
with open("/root/psvibe-sales-bot/customer_bot/booking.py", "r") as f:
    content = f.read()

old5 = """    # For pending bookings, console_id may store the type (e.g. "PS5", "PS5 Pro")
    # For confirmed bookings, console_id is the specific console (e.g. "C - 01")
    # Prefer consoleType (user-friendly), fall back to console_id, "PS5" default
    raw_console = b.get("consoleType") or b.get("console_id") or ""
    if not str(raw_console).strip():
        raw_console = "PS5"
    console_type = str(raw_console)"""

new5 = """    # For pending bookings, console_id stores the type (e.g. "PS5", "PS5 Pro")
    # For confirmed bookings, console_id is the specific console (e.g. "C - 01")
    # Use console_id first; if empty, fall back to "PS5"
    raw_console = b.get("console_id") or b.get("consoleType") or ""
    if not str(raw_console).strip():
        raw_console = "PS5"
    console_type = str(raw_console)"""

if old5 in content:
    content = content.replace(old5, new5)
    print("FIX 5 APPLIED: booking.py console order")
else:
    print("FIX 5 SKIPPED: pattern not found - trying alternative")
    # Try to find it another way
    if "raw_console = b.get" in content:
        print("  Found raw_console, content has it")

with open("/root/psvibe-sales-bot/customer_bot/booking.py", "w") as f:
    f.write(content)

import subprocess
r = subprocess.run(["python3", "-m", "py_compile", "/root/psvibe-sales-bot/customer_bot/booking.py"],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("VERIFY 5: py_compile PASS")
else:
    print("VERIFY 5: py_compile FAIL: " + r.stderr[:200])

# ── FIX 6: app.py — fix hardcoded consoleType in api_search_bookings ──
with open("/root/psvibe_api_server/app.py", "r") as f:
    app_content = f.read()

# Find the hardcoded "consoleType": "PS5" in the normalize loop
old6 = '''            normalized.append({"id": r.get("id",""), "customerName": r.get("staff_name",""), "phone": r.get("phone","") or r.get("telegram_chat_id",""), "date": bd_str, "timeSlot": time_slot, "consoleType": "PS5", "durationMins": r.get("duration_mins",60), "gameName": r.get("game_name",""), "console_id": r.get("console_id",""), "consoleId": r.get("console_id",""), "member_id": r.get("member_id",""), "status": r.get("status","")})'''

new6 = '''            # Derive consoleType from console_id: if console_id is a specific ID (C-01, etc),
            # try to match against console_status; otherwise use console_id as the type name
            _cid = r.get("console_id", "")
            _ctype = _cid  # default: use console_id as display type (works for "PS5", "PS5 Pro")
            # If console_id looks like a specific console ID (e.g., "C - 01", "C-01"),
            # try to resolve to a type name from console_status
            if _cid and not any(t in _cid.lower() for t in ("ps5", "ps4", "ps3", "xbox", "switch", "pc")):
                try:
                    _crows = _mysql_query("SELECT console_type FROM console_status WHERE console_id=%s LIMIT 1", (_cid,))
                    if _crows and _crows[0].get("console_type"):
                        _ctype = _crows[0]["console_type"]
                except Exception:
                    pass
            normalized.append({"id": r.get("id",""), "customerName": r.get("staff_name",""), "phone": r.get("phone","") or r.get("telegram_chat_id",""), "date": bd_str, "timeSlot": time_slot, "consoleType": _ctype, "durationMins": r.get("duration_mins",60), "gameName": r.get("game_name",""), "console_id": r.get("console_id",""), "consoleId": r.get("console_id",""), "member_id": r.get("member_id",""), "status": r.get("status","")})'''

if old6 in app_content:
    app_content = app_content.replace(old6, new6)
    print("FIX 6 APPLIED: app.py consoleType derivation")
else:
    print("FIX 6 SKIPPED: pattern not found in app.py - may need manual check")
    # Check if there's a variation
    if '"consoleType": "PS5"' in app_content:
        print("  Found hardcoded consoleType, trying alternative match...")
        # The pattern might have slightly different whitespace
        import re
        match = re.search(r'"consoleType":\s*"PS5"', app_content)
        if match:
            print(f"  Found at position {match.start()}")

with open("/root/psvibe_api_server/app.py", "w") as f:
    f.write(app_content)

r2 = subprocess.run(["python3", "-m", "py_compile", "/root/psvibe_api_server/app.py"],
                    capture_output=True, text=True)
if r2.returncode == 0:
    print("VERIFY 6: app.py py_compile PASS")
else:
    print("VERIFY 6: app.py py_compile FAIL: " + r2.stderr[:200])

print("ALL FIXES DONE")
PYEOF`;

  conn.exec(fixCmd, (err, stream) => {
    let out = '';
    stream.on('data', c => out += c);
    stream.stderr.on('data', c => out += c);
    stream.on('close', () => {
      console.log('FIX OUTPUT:\n' + out);
      
      // Verify final state
      conn.exec('grep -A 15 "raw_console = " /root/psvibe-sales-bot/customer_bot/booking.py', (e2, s2) => {
        let o2 = ''; s2.on('data', c => o2 += c);
        s2.on('close', () => {
          console.log('\n=== FINAL booking.py console handling ===\n' + o2);
          conn.end();
        });
      });
    });
  });
});

conn.on('error', (err) => { console.error('SSH ERROR:', err.message); process.exit(1); });
conn.connect({host:'5.223.81.16',port:22,username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),readyTimeout:15000});
