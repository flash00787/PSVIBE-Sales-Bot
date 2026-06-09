const { Client } = require('ssh2');
const fs = require('fs');
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();
conn.on('ready', () => {
  const cmd = `cat > /tmp/stats.py << 'PYEOF'
import json
with open("/root/coordination/findings/arch_data.json") as f:
    d = json.load(f)
unique = set()
for c in d["circular_deps"]:
    unique.add(frozenset(c))
print("modules:", d["total_modules"])
print("imports:", d["total_imports"])
print("edges:", len(d["edges"]))
print("circular_deps_raw:", len(d["circular_deps"]))
print("circular_deps_unique:", len(unique))
print("star_imports:", len(d["star_imports"]))
print("unused_imports:", len(d["unused_imports"]))
print("max_chain_depth:", d["max_chain_depth"])
PYEOF
python3 /tmp/stats.py`;
  
  conn.exec(cmd, (err, stream) => {
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => process.stderr.write(d.toString()));
    stream.on('close', () => { console.log(out.trim()); conn.end(); });
  });
});
conn.on('error', e => { console.error(e); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync(KEY_PATH) });
