const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();

conn.on('ready', () => {
  conn.exec('grep -n \'consoleType.*PS5\\|"consoleType":\' /root/psvibe_api_server/app.py | head -20', (err, s) => {
    let d=''; s.on('data',c=>d+=c);
    s.on('close',()=>{
      console.log('MATCHES:\n'+d);
      
      // Fix: replace ALL occurrences of hardcoded consoleType
      const fixAll = `python3 << 'PYEOF'
with open("/root/psvibe_api_server/app.py", "r") as f:
    content = f.read()

# Count occurrences
count = content.count(\'"consoleType": "PS5"\')
print(f"Found {count} occurrences of hardcoded consoleType")

# Replace ALL occurrences of the hardcoded consoleType in the normalized.append lines
# Use a more targeted approach - find and fix each normalized.append
import re

# Pattern: the normalized.append line with hardcoded consoleType
# We need to replace "consoleType": "PS5" with consoleType derivation
# But we can't easily do it inline, so let's use a different approach
# Replace the hardcoded value with a function call

# First, let's find the exact lines
lines = content.split("\\n")
fixed_lines = []
in_normalize = False
for i, line in enumerate(lines):
    if "normalized.append" in line and '"consoleType": "PS5"' in line:
        print(f"Fixing line {i+1}: {line.strip()[:80]}...")
        # Add the console type derivation BEFORE the append, then fix the line
        # Strategy: add derivation code before the normalized.append, then replace "PS5" with _ctype
        
        # Replace hardcoded "PS5" with _ctype reference  
        line = line.replace('"consoleType": "PS5"', '"consoleType": _ctype')
        fixed_lines.append(line)
    else:
        fixed_lines.append(line)

# Now add the _ctype derivation code before the first normalized.append
# Find the for loop that iterates rows and add derivation inside
content = "\\n".join(fixed_lines)

# Add consoleType derivation before each normalized.append that uses _ctype
# We need to add the derivation code in the for loop
new_content = []
for i, line in enumerate(content.split("\\n")):
    new_content.append(line)
    # After a line that has "normalized.append" with "_ctype", 
    # we need to make sure the derivation was added before the loop
    # Actually, let's add it before each append that needs it

# Better approach: find the for loop and add derivation at the start
# Find "for r in rows:" and add the _ctype derivation after it
content = content.replace(
    'for r in rows:\\n            start = r.get("start_time")',
    'for r in rows:\\n            # Derive consoleType from console_id\\n            _cid = r.get("console_id", "")\\n            _ctype = _cid\\n            if _cid and not any(t in _cid.lower() for t in ("ps5", "ps4", "ps3", "xbox", "switch", "pc")):\\n                try:\\n                    _crows = _mysql_query("SELECT console_type FROM console_status WHERE console_id=%s LIMIT 1", (_cid,))\\n                    if _crows and _crows[0].get("console_type"):\\n                        _ctype = _crows[0]["console_type"]\\n                except Exception:\\n                    pass\\n            start = r.get("start_time")'
)

with open("/root/psvibe_api_server/app.py", "w") as f:
    f.write(content)

# Verify
import subprocess
r = subprocess.run(["python3", "-m", "py_compile", "/root/psvibe_api_server/app.py"],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("PY_COMPILE: PASS")
else:
    print("PY_COMPILE: FAIL")
    print(r.stderr[:300])

# Count remaining hardcoded
with open("/root/psvibe_api_server/app.py", "r") as f:
    c2 = f.read()
remaining = c2.count(\'"consoleType": "PS5"\')
print(f"Remaining hardcoded consoleType: {remaining}")
print("DONE")
PYEOF`;

      conn.exec(fixAll, (e2, s2) => {
        let d2=''; s2.on('data',c=>d2+=c); s2.stderr.on('data',c=>d2+=c);
        s2.on('close',()=>{
          console.log('\nFIX ALL:\n'+d2);
          
          // Restart API and verify
          conn.exec('timeout 15 systemctl restart psvibe-api && echo "OK" || echo "TIMEOUT"; sleep 2; curl -s --max-time 5 "http://localhost:8000/api/bookings/search?telegram_chat_id=6296803251" -H "X-API-Key: JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" | python3 -c "import sys,json; d=json.load(sys.stdin); bks=d.get(\"data\",{}).get(\"bookings\",[]); [print(f\'consoleType={b.get(\"consoleType\",\"MISSING\")} console_id={b.get(\"console_id\",\"?\")}\') for b in bks[:3]]" 2>&1', (e3, s3) => {
            let d3=''; s3.on('data',c=>d3+=c); s3.stderr.on('data',c=>d3+=c);
            s3.on('close',()=>{
              console.log('\nVERIFY:\n'+d3);
              conn.end();
            });
          });
        });
      });
    });
  });
});
conn.connect({host:'5.223.81.16',port:22,username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),readyTimeout:15000});
