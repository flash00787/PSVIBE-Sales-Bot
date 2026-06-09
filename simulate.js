const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Insert a test pending booking  
  'mysql -upsvibe_user -pPsVibe@2026_Rotated! -h 127.0.0.1 psvibe_api -e "INSERT INTO console_booking (console_id, member_id, booking_date, start_time, end_time, status, staff_name, notes, telegram_chat_id, duration_mins, phone, game_name) VALUES (\'\', \'6296803251\', \'2026-06-03\', \'2026-06-03 18:00:00\', \'2026-06-03 19:00:00\', \'pending\', \'Test Customer\', \'Game: FIFA 23 | Phone: 09123456789\', \'6296803251\', 60, \'09123456789\', \'FIFA 23\')" 2>&1',
  // Simulate what _replit_get returns (the raw JSON)
  'curl -s "http://localhost:8000/api/bookings?status=pending" -H "X-API-Key: JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" > /tmp/bookings_raw.json && python3 -c " 
import json
with open(\"/tmp/bookings_raw.json\") as f:
    data = json.load(f)
print(\"RAW response:\")
print(json.dumps(data, indent=2))
print()
print(\"=== Simulating _replit_get unwrap ===\")
is_list_path = True
inner = data.get(\"data\")
print(f\"inner: {type(inner).__name__} = {json.dumps(inner, indent=2)}\")
if isinstance(inner, dict):
    for lk in (\"bookings\", \"items\", \"members\"):
        if lk in inner and isinstance(inner[lk], list):
            result = inner[lk]
            print(f\"Unwrapped via key \\\"{lk}\\\": {type(result).__name__}")
            break
    else:
        result = inner
else:
    result = inner
print()
print(\"=== Simulating cmd_admin_bookings ===\")
bookings = result
print(f\"bookings: {type(bookings).__name__} of len {len(bookings)}\")
if not bookings:
    print(\"No pending bookings\")
else:
    for b in bookings:
        print(f\"\\nBooking #{b.get(\\\"id\\\")}:\")
        print(f\"  customerName: {b.get(\\\"customerName\\\")}\")
        print(f\"  phone: {b.get(\\\"phone\\\")}\")
        print(f\"  date: {b.get(\\\"date\\\")}\")
        print(f\"  timeSlot: {b.get(\\\"timeSlot\\\")}\")
        print(f\"  consoleType: {b.get(\\\"consoleType\\\")}\")
        print(f\"  durationMins: {b.get(\\\"durationMins\\\")}\")
        print(f\"  gameName: {b.get(\\\"gameName\\\")}\")
        card = f\"🎫 *Booking #{b[\\\"id\\\"]}*\\n\" + \\
               f\"👤 {b.get(\\\"customerName\\\", \\\"Unknown\\\")}  📞 {b.get(\\\"phone\\\", \\\"-\\\")}\\n\" + \\
               f\"📅 {b.get(\\\"date\\\", \\\"?\\\")}  🕐 {b.get(\\\"timeSlot\\\", \\\"?\\\")}\\n\" + \\
               f\"🎮 {b.get(\\\"consoleType\\\", \\\"-\\\")}  ⏱️ {b.get(\\\"durationMins\\\", \\\"?\\\")} mins\\n\"
        print(f\"  CARD: {card}\")
"
  ' 2>&1',
  // Clean up
  'mysql -upsvibe_user -pPsVibe@2026_Rotated! -h 127.0.0.1 psvibe_api -e "DELETE FROM console_booking WHERE staff_name=\'Test Customer\'" 2>&1',
];

let results = {};
let cmdIdx = 0;

conn.on('ready', () => runNext());
function runNext() {
  if (cmdIdx >= commands.length) { conn.end(); console.log(JSON.stringify(results, null, 2)); return; }
  const cmd = commands[cmdIdx];
  const label = cmdIdx.toString();
  conn.exec(cmd, (err, stream) => {
    if (err) { results[label] = { cmd, stdout: '', stderr: 'ERROR: ' + err.message }; cmdIdx++; runNext(); return; }
    let stdout = '', stderr = '';
    stream.on('data', d => stdout += d.toString());
    stream.stderr.on('data', d => stderr += d.toString());
    stream.on('close', () => { results[label] = { cmd, stdout, stderr }; cmdIdx++; runNext(); });
  });
}
conn.connect({ host: '5.223.81.16', username: 'root', privateKey: key, readyTimeout: 15000 });
conn.on('error', (err) => { console.error('SSH ERROR:', err.message); process.exit(1); });
