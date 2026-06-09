const { Client } = require('ssh2');
const fs = require('fs');

const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

function runCmd(conn, cmd, label) {
  return new Promise((resolve, reject) => {
    const t = Date.now();
    conn.exec(cmd, (err, stream) => {
      if (err) { reject(err); return; }
      let out = '';
      stream.on('data', d => out += d.toString());
      stream.stderr.on('data', d => out += '[STDERR] ' + d.toString());
      stream.on('close', code => {
        const elapsed = Date.now() - t;
        resolve({ label, out: out.trim(), code, elapsed });
      });
    });
  });
}

async function main() {
  const conn = new Client();
  
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync(KEY_PATH) });
  });
  
  console.log('SSH:CONNECTED\n');
  
  const tests = [
    { label: 'TEST 1: Syntax', cmd: 'python3 -m py_compile /root/coordination/arch_mapper.py && echo "PASS" || echo "FAIL"' },
    { label: 'TEST 2: Dep Text', cmd: 'python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --dep-text /root/coordination/findings/arch_report.txt 2>&1' },
    { label: 'TEST 3: Mermaid', cmd: 'python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --graph /root/coordination/findings/arch_diagram.md 2>&1' },
    { label: 'TEST 4: Circular', cmd: 'python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --circular 2>&1' },
    { label: 'TEST 5: JSON', cmd: 'python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --json /root/coordination/findings/arch_data.json 2>&1' },
    { label: 'TEST 6: DOT', cmd: 'python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --dot /root/coordination/findings/arch_graph.dot 2>&1' },
  ];
  
  for (const t of tests) {
    console.log(`--- ${t.label} ---`);
    const result = await runCmd(conn, t.cmd, t.label);
    console.log(result.out);
    console.log(`(exit: ${result.code}, ${result.elapsed}ms)\n`);
  }
  
  conn.end();
  console.log('ALL TESTS DONE');
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
