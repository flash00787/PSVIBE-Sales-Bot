const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();

conn.on('ready', () => {
  const fixCmd = `python3 << 'PYEOF'
with open("/root/psvibe_api_server/app.py", "r") as f:
    content = f.read()

# Add consoleType to the search endpoint's normalized.append dict
# Find the multi-line normalized.append in api_search_bookings 
old_search = '''            normalized.append({
                "id": r.get("id"),
                "console_id": r.get("console_id"),
                "member_id": r.get("member_id"),
                "booking_date": str(r.get("booking_date", "")),
                "timeSlot": time_slot,
                "startTime": str(r.get("start_time", "")),
                "endTime": str(r.get("end_time", "")),
                "status": r.get("status", "pending"),
                "staff_name": r.get("staff_name"),
                "notes": r.get("notes"),
                "telegram_chat_id": r.get("telegram_chat_id"),
                "durationMins": duration,
                "duration_mins": duration,
                "gameName": game_name,
                "game_name": game_name,
                "phone": r.get("phone"),
            })'''

new_search = '''            normalized.append({
                "id": r.get("id"),
                "console_id": r.get("console_id"),
                "consoleType": _ctype,
                "member_id": r.get("member_id"),
                "booking_date": str(r.get("booking_date", "")),
                "timeSlot": time_slot,
                "startTime": str(r.get("start_time", "")),
                "endTime": str(r.get("end_time", "")),
                "status": r.get("status", "pending"),
                "staff_name": r.get("staff_name"),
                "notes": r.get("notes"),
                "telegram_chat_id": r.get("telegram_chat_id"),
                "durationMins": duration,
                "duration_mins": duration,
                "gameName": game_name,
                "game_name": game_name,
                "phone": r.get("phone"),
            })'''

if old_search in content:
    content = content.replace(old_search, new_search)
    print("FIX 7 APPLIED: Added consoleType to search endpoint")
else:
    print("FIX 7 SKIPPED: pattern not found")
    # Try to find it anyway
    if "timeSlot": time_slot,\n                "startTime"" in content.replace(" ", ""):
        print("  Pattern might be there but with different whitespace")

with open("/root/psvibe_api_server/app.py", "w") as f:
    f.write(content)

import subprocess
r = subprocess.run(["python3", "-m", "py_compile", "/root/psvibe_api_server/app.py"],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("PY_COMPILE: PASS")
else:
    print("PY_COMPILE: FAIL: " + r.stderr[:300])

print("DONE")
PYEOF`;

  conn.exec(fixCmd, (err, s) => {
    let d=''; s.on('data',c=>d+=c); s.stderr.on('data',c=>d+=c);
    s.on('close',()=>{
      console.log('FIX:\n'+d);
      
      // Restart API and verify
      conn.exec('timeout 15 systemctl restart psvibe-api && sleep 2 && curl -s --max-time 5 "http://localhost:8000/api/bookings/search?telegram_chat_id=6296803251" -H "X-API-Key: JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" | python3 -c "import sys,json; d=json.load(sys.stdin); bks=d.get(\"data\",{}).get(\"bookings\",[]); [print(\"consoleType=\" + str(b.get(\"consoleType\",\"MISSING\")) + \" console_id=\" + str(b.get(\"console_id\",\"?\"))) for b in bks[:3]]" 2>&1', (e2, s2) => {
        let d2=''; s2.on('data',c=>d2+=c); s2.stderr.on('data',c=>d2+=c);
        s2.on('close',()=>{
          console.log('VERIFY:\n'+d2);
          conn.end();
        });
      });
    });
  });
});
conn.connect({host:'5.223.81.16',port:22,username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),readyTimeout:15000});
