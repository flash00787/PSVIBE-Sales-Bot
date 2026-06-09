const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

conn.on('ready', () => {
  console.log('SSH:CONNECTED');
  
  const content = fs.readFileSync('/home/node/.openclaw/workspace/arch_mapper.py');
  const b64 = content.toString('base64');
  
  // Step 1: Transfer file via base64
  conn.exec(`mkdir -p /root/coordination/findings && echo "${b64}" | base64 -d > /root/coordination/arch_mapper.py && echo "UPLOAD_OK" && wc -l /root/coordination/arch_mapper.py`, (err, stream) => {
    if (err) { console.log('ERROR_UPLOAD:', err.message); conn.end(); return; }
    let uploadOut = '';
    stream.on('data', d => uploadOut += d.toString());
    stream.stderr.on('data', d => process.stderr.write('E_UPLOAD:' + d.toString()));
    stream.on('close', (code) => {
      console.log('UPLOAD:', uploadOut.trim());
      if (code !== 0) { console.log('Upload failed with code', code); conn.end(); return; }
      
      // Step 2: Run tests
      const tests = `
echo "=== TEST 1: Syntax ==="
python3 -m py_compile /root/coordination/arch_mapper.py && echo "PASS" || echo "FAIL"

echo "=== TEST 2: Dep Text ==="
python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --dep-text /root/coordination/findings/arch_report.txt 2>&1

echo "=== TEST 3: Mermaid ==="
python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --graph /root/coordination/findings/arch_diagram.md 2>&1

echo "=== TEST 4: Circular ==="
python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --circular 2>&1

echo "=== TEST 5: JSON ==="
python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --json /root/coordination/findings/arch_data.json 2>&1

echo "=== TEST 6: DOT ==="
python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --dot /root/coordination/findings/arch_graph.dot 2>&1

echo "=== ALL TESTS DONE ==="
`;
      
      conn.exec(tests, (err2, stream2) => {
        if (err2) { console.log('ERROR_TESTS:', err2.message); conn.end(); return; }
        let out2 = '';
        stream2.on('data', d => out2 += d.toString());
        stream2.stderr.on('data', d => process.stderr.write('E_TESTS:' + d.toString()));
        stream2.on('close', (code2) => {
          console.log('\\n' + out2);
          console.log('TEST_EXIT:', code2);
          conn.end();
        });
      });
    });
  });
});

conn.on('error', (err) => { console.error('SSH_ERROR:', err.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync(KEY_PATH) });
