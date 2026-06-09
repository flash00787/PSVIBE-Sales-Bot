const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

conn.on('ready', () => {
  conn.exec('python3 -c "
import json,sys
d = json.load(sys.stdin)
keys = list(d.keys())
print('=== KEYS ===', keys)
funcs = d.get('functions', [])
print('=== FUNCTIONS (first 40) ===')
for f in funcs[:40]:
    if isinstance(f, dict):
        n = f.get('name','?')
        fl = f.get('file','')
        t = f.get('type','')
        p = f.get('params','')
        print(f'{n:35s} | {fl:25s} | {t:10s} | {str(p)[:40]}')
    else:
        print(f)
print(f'\nTotal: {len(funcs)} functions')
" 2>&1 < /root/agent_output/function_map.json', (err, stream) => {
    if (err) { console.error(err); process.exit(1); }
    let o = '';
    stream.on('data', d => o += d.toString());
    stream.stderr.on('data', d => o += d.toString());
    stream.on('close', () => { console.log(o); conn.end(); process.exit(0); });
  });
}).connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: key });
