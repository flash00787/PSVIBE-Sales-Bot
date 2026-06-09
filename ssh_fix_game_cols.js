const { Client } = require('ssh2');
const fs = require('fs');

const commands = [
  // 1. Backup original
  'cp /root/psvibe_api_server/app.py /root/psvibe_api_server/app.py.bak_$(date +%Y%m%d_%H%M%S)',

  // 2. Apply fix: replace the game dict in api_fetch_games()
  // Old: platform/row[2], genre/row[3], status/row[4], discs/row[5]
  // New: status/row[2], discs/row[3], in_use/row[4], platform="PS5", genre/row[20]
  `python3 -c "
import re
with open('/root/psvibe_api_server/app.py', 'r') as f:
    content = f.read()

old = '''            games.append({
                \\\"row\\\": i,
                \\\"title\\\": row[1].strip() if len(row) > 1 else \\\"\\\",
                \\\"platform\\\": row[2].strip() if len(row) > 2 else \\\"\\\",
                \\\"genre\\\": row[3].strip() if len(row) > 3 else \\\"\\\",
                \\\"status\\\": row[4].strip() if len(row) > 4 else \\\"\\\",
                \\\"discs\\\": row[5].strip() if len(row) > 5 else \\\"\\\",
            })'''

new = '''            games.append({
                \\\"row\\\": i,
                \\\"title\\\": row[1].strip() if len(row) > 1 else \\\"\\\",
                \\\"status\\\": row[2].strip() if len(row) > 2 else \\\"\\\",
                \\\"discs\\\": row[3].strip() if len(row) > 3 else \\\"\\\",
                \\\"in_use\\\": row[4].strip() if len(row) > 4 else \\\"0\\\",
                \\\"platform\\\": \\\"PS5\\\",
                \\\"genre\\\": row[20].strip() if len(row) > 20 else \\\"\\\",
            })
        # Parse genre from col U metadata (\\\"solo_multi|genre\\\" format)
        for g in games:
            meta = g.get(\\\"genre\\\", \\\"\\\")
            if \\\"|\\\" in meta:
                parts = meta.split(\\\"|\\\", 1)
                g[\\\"solo_multi\\\"] = parts[0].strip()
                g[\\\"genre\\\"] = parts[1].strip()'''

if old not in content:
    print('ERROR: Old pattern not found in app.py')
    exit(1)

content = content.replace(old, new)

with open('/root/psvibe_api_server/app.py', 'w') as f:
    f.write(content)

print('OK: Fix applied to app.py')
" 2>&1`,

  // 3. Verify the fix
  `python3 -c "
with open('/root/psvibe_api_server/app.py', 'r') as f:
    content = f.read()
# Check new fields exist
checks = ['\\\"status\\\": row[2]', '\\\"discs\\\": row[3]', '\\\"in_use\\\": row[4]', '\\\"platform\\\": \\\"PS5\\\"', '\\\"genre\\\": row[20]']
for c in checks:
    if c in content:
        print(f'  ✅ Found: {c}')
    else:
        print(f'  ❌ MISSING: {c}')
# Check old fields gone
old_checks = ['\\\"platform\\\": row[2]', '\\\"genre\\\": row[3]', '\\\"status\\\": row[4]', '\\\"discs\\\": row[5]']
for c in old_checks:
    if c in content:
        print(f'  ❌ STILL PRESENT: {c}')
    else:
        print(f'  ✅ Removed: {c}')
print('VERIFICATION DONE')
" 2>&1`,

  // 4. Compile check
  'cd /root/psvibe_api_server && python3 -m py_compile app.py 2>&1 && echo "COMPILE: OK" || echo "COMPILE: FAILED"',

  // 5. Restart API
  'systemctl restart psvibe-api 2>&1 && echo "RESTART: OK" || echo "RESTART: FAILED"',

  // 6. Wait and test
  'sleep 2 && curl -s "http://localhost:8000/api/fetch_games" 2>&1 | python3 -m json.tool 2>&1 | head -40',
];

let idx = 0;
function runNext(conn) {
  if (idx >= commands.length) {
    conn.end();
    process.exit(0);
  }
  const cmd = commands[idx++];
  console.log(`\n=== CMD ${idx}: ${cmd.substring(0, 80)}... ===`);
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC ERROR:', err.message); conn.end(); process.exit(1); }
    let out = '';
    stream.on('close', (code) => {
      console.log(out);
      if (code !== 0 && idx <= 4) {
        console.error(`Command ${idx} failed with code ${code}`);
      }
      runNext(conn);
    }).on('data', (d) => { out += d.toString(); })
      .stderr.on('data', (d) => { out += d.toString(); });
  });
}

const conn = new Client();
conn.on('ready', () => runNext(conn))
  .on('error', (err) => { console.error('SSH ERROR:', err.message); process.exit(1); })
  .connect({
    host: '5.223.81.16',
    port: 22,
    username: 'root',
    privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
  });
