const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

conn.on('ready', () => {
  console.log('SSH:CONNECTED');
  
  const mapperContent = fs.readFileSync('/home/node/.openclaw/workspace/arch_mapper.py', 'utf-8');
  
  const cmd = `mkdir -p /root/coordination/findings && cat > /root/coordination/arch_mapper.py << 'PYEOF'
${mapperContent}
PYEOF
echo "UPLOAD_OK"

echo "=== TEST 1: Syntax Check ==="
python3 -m py_compile /root/coordination/arch_mapper.py && echo "PASS" || echo "FAIL"

echo "=== TEST 2: Dep Text Report ==="
python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --dep-text /root/coordination/findings/arch_report.txt 2>&1

echo "=== TEST 3: Mermaid Graph ==="
python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --graph /root/coordination/findings/arch_diagram.md 2>&1

echo "=== TEST 4: Circular Dep Check ==="
python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --circular 2>&1

echo "=== TEST 5: JSON Output ==="
python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --json /root/coordination/findings/arch_data.json 2>&1

echo "=== TEST 6: DOT Graph ==="
python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --dot /root/coordination/findings/arch_graph.dot 2>&1

echo "=== ALL TESTS DONE ==="
`;

  conn.exec(cmd, (err, stream) => {
    if (err) { console.log('ERROR:', err.message); conn.end(); return; }
    let data = '';
    stream.on('data', d => data += d.toString());
    stream.stderr.on('data', d => process.stderr.write('E:' + d.toString()));
    stream.on('close', (code) => {
      console.log(data);
      console.log('EXIT:', code);
      conn.end();
    });
  });
});

conn.on('error', (err) => { console.error('SSH_ERROR:', err.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync(KEY_PATH) });
