const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
let pending = 0;
let allResults = [];

function runCmd(cmd, label) {
  return new Promise((resolve) => {
    pending++;
    conn.exec(cmd, (err, stream) => {
      if (err) { allResults.push(`${label}: SSH ERR ${err.message}`); pending--; resolve(); return; }
      let out = '', errOut = '';
      stream.on('data', (d) => out += d.toString());
      stream.stderr.on('data', (d) => errOut += d.toString());
      stream.on('close', (code) => {
        allResults.push(`${label}: code=${code}\nSTDOUT: ${out}\nSTDERR: ${errOut}`);
        pending--;
        resolve();
      });
    });
  });
}

conn.on('ready', async () => {
  console.log('Connected to VPS');

  // 1. Fix api.py _fetch_games_full — multi-line replacement using Python with exact line numbers
  await runCmd(
    `python3 << 'PYEOF'
with open('/root/psvibe-sales-bot/customer_bot/api.py', 'r') as f:
    lines = f.readlines()

# Line 275 (0-indexed: 274) — replace single line with multi-line block
target_line = '        games = (data or {}).get("data", [])\n'
replacement = """        if isinstance(data, list):
            games = data
        elif isinstance(data, dict):
            games = data.get("data", [])
        else:
            games = []
"""

for i, line in enumerate(lines):
    if line == target_line:
        lines[i] = replacement
        print(f'FIXED _fetch_games_full at line {i+1}')
        break
else:
    print('SKIP: _fetch_games_full pattern not found')
    # Debug: show surrounding context
    for i, line in enumerate(lines):
        if 'games = (data or {}).get' in line:
            print(f'Similar line at {i+1}: {repr(line)}')

with open('/root/psvibe-sales-bot/customer_bot/api.py', 'w') as f:
    f.writelines(lines)
PYEOF`,
    'api.py: _fetch_games_full (round 2)'
  );

  // 2. Fix api.py _fetch_promotions
  await runCmd(
    `python3 << 'PYEOF'
with open('/root/psvibe-sales-bot/customer_bot/api.py', 'r') as f:
    lines = f.readlines()

target_line = '        promos = (data or {}).get("data", [])\n'
replacement = """        if isinstance(data, list):
            promos = data
        elif isinstance(data, dict):
            promos = data.get("data", [])
        else:
            promos = []
"""

for i, line in enumerate(lines):
    if line == target_line:
        lines[i] = replacement
        print(f'FIXED _fetch_promotions at line {i+1}')
        break
else:
    print('SKIP: _fetch_promotions pattern not found')

with open('/root/psvibe-sales-bot/customer_bot/api.py', 'w') as f:
    f.writelines(lines)
PYEOF`,
    'api.py: _fetch_promotions (round 2)'
  );

  // 3. Fix booking_handlers.py _get_available_slots — simple sed
  await runCmd(
    `sed -i 's|bookings?date=|bookings/search?date=|g' /root/psvibe-sales-bot/customer_bot/booking_handlers.py && echo "FIXED: _get_available_slots endpoint"`,
    'booking_handlers.py: endpoint fix'
  );

  // 4. Fix booking_handlers.py bk_confirm — camelCase fix + endpoint
  await runCmd(
    `sed -i 's|bookings?telegramChatId=|bookings/search?telegram_chat_id=|g' /root/psvibe-sales-bot/customer_bot/booking_handlers.py && echo "FIXED: bk_confirm camelCase + endpoint"`,
    'booking_handlers.py: camelCase fix'
  );

  while (pending > 0) {
    await new Promise(r => setTimeout(r, 200));
  }
  
  fs.writeFileSync('/home/node/.openclaw/workspace/temp/fix_results_r2.json', JSON.stringify(allResults, null, 2));
  console.log('ALL DONE round 2');
  conn.end();
});

conn.on('error', (err) => { console.error('SSH error:', err); process.exit(1); });

conn.connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
