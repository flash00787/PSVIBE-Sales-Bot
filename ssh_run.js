const { Client } = require('ssh2');
const fs = require('fs');

const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH:CONNECTED');
  
  // Write test runner script
  const runner = `#!/bin/bash
set -e
cd /root/coordination

echo "===TEST1_START==="
python3 -m py_compile arch_mapper.py && echo "TEST1:PASS" || echo "TEST1:FAIL"
echo "===TEST1_END==="

echo "===TEST2_START==="
python3 arch_mapper.py --bot-dir /root/psvibe-sales-bot --dep-text findings/arch_report.txt 2>&1
echo "===TEST2_END==="

echo "===TEST3_START==="
python3 arch_mapper.py --bot-dir /root/psvibe-sales-bot --graph findings/arch_diagram.md 2>&1
echo "===TEST3_END==="

echo "===TEST4_START==="
python3 arch_mapper.py --bot-dir /root/psvibe-sales-bot --circular 2>&1
echo "===TEST4_END==="

echo "===TEST5_START==="
python3 arch_mapper.py --bot-dir /root/psvibe-sales-bot --json findings/arch_data.json 2>&1
echo "===TEST5_END==="

echo "===TEST6_START==="
python3 arch_mapper.py --bot-dir /root/psvibe-sales-bot --dot findings/arch_graph.dot 2>&1
echo "===TEST6_END==="

echo "===ALL_DONE==="
`;
  
  conn.exec(`cat > /root/coordination/run_tests.sh << 'SHEOF'
${runner}
SHEOF
chmod +x /root/coordination/run_tests.sh
echo "RUNNER_CREATED"`, (err, stream) => {
    if (err) { console.log('ERR:', err.message); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.on('close', () => {
      console.log(out.trim());
      
      // Now run it with timeout
      conn.exec('timeout 180 bash /root/coordination/run_tests.sh 2>&1', (err2, stream2) => {
        if (err2) { console.log('ERR2:', err2.message); conn.end(); return; }
        let out2 = '';
        stream2.on('data', d => out2 += d.toString());
        stream2.stderr.on('data', d => out2 += d.toString());
        stream2.on('close', (code2) => {
          console.log('\n' + out2);
          console.log('\nEXIT:', code2);
          conn.end();
        });
      });
    });
  });
});

conn.on('error', (err) => { console.error('SSH_ERR:', err.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync(KEY_PATH) });
