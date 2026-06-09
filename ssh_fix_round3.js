const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
let pending = 0;
let allResults = [];

function runCmd(cmd, label) {
  return new Promise((resolve) => {
    pending++;
    conn.exec(cmd, (err, stream) => {
      if (err) { allResults.push(`${label}: ERR ${err.message}`); pending--; resolve(); return; }
      let out = '', errOut = '';
      stream.on('data', (d) => out += d.toString());
      stream.stderr.on('data', (d) => errOut += d.toString());
      stream.on('close', (code) => {
        allResults.push(`${label}: code=${code}\n${out}${errOut}`);
        pending--;
        resolve();
      });
    });
  });
}

conn.on('ready', async () => {
  console.log('Connected');

  // Write fix script for api.py to /tmp on VPS
  const fixScript1 = `import sys
with open('/root/psvibe-sales-bot/customer_bot/api.py', 'r') as f:
    lines = f.readlines()

fixes = 0
for i, line in enumerate(lines):
    if line == '        games = (data or {}).get("data", [])\\n':
        lines[i] = '        if isinstance(data, list):\\n            games = data\\n        elif isinstance(data, dict):\\n            games = data.get("data", [])\\n        else:\\n            games = []\\n'
        print(f'FIXED _fetch_games_full at line {i+1}')
        fixes += 1
    elif line == '        promos = (data or {}).get("data", [])\\n':
        lines[i] = '        if isinstance(data, list):\\n            promos = data\\n        elif isinstance(data, dict):\\n            promos = data.get("data", [])\\n        else:\\n            promos = []\\n'
        print(f'FIXED _fetch_promotions at line {i+1}')
        fixes += 1

if fixes == 0:
    print('NO FIXES APPLIED - checking patterns:')
    for i, line in enumerate(lines):
        if 'games = (data' in line:
            print(f'Line {i+1}: {repr(line)}')
        if 'promos = (data' in line:
            print(f'Line {i+1}: {repr(line)}')
else:
    with open('/root/psvibe-sales-bot/customer_bot/api.py', 'w') as f:
        f.writelines(lines)
    print(f'Total fixes: {fixes}')
`;

  // Write script to VPS
  await runCmd(`cat > /tmp/fix_api.py << 'ENDOFPYTHON'\n${fixScript1}\nENDOFPYTHON`, 'write fix script');
  
  // Execute it
  await runCmd('python3 /tmp/fix_api.py', 'run fix_api.py');

  while (pending > 0) { await new Promise(r => setTimeout(r, 100)); }
  
  fs.writeFileSync('/home/node/.openclaw/workspace/temp/fix_results_r3.json', JSON.stringify(allResults, null, 2));
  console.log('ALL DONE round 3');
  conn.end();
});

conn.on('error', (err) => { console.error('Error:', err); process.exit(1); });
conn.connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
