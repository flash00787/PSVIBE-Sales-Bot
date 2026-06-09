const { Client } = require('ssh2');
const fs = require('fs');

const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

function execCmd(conn, cmd) {
  return new Promise((resolve) => {
    conn.exec(cmd, (err, stream) => {
      if (err) { resolve(`ERROR: ${err.message}`); return; }
      let d = '';
      stream.on('data', dd => d += dd.toString());
      stream.stderr.on('data', dd => d += dd.toString());
      stream.on('close', (c) => resolve({ out: d.trim(), code: c }));
    });
  });
}

async function main() {
  const conn = new Client();
  await new Promise((res, rej) => {
    conn.on('ready', res);
    conn.on('error', rej);
    conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync(KEY_PATH) });
  });
  console.log('SSH:CONNECTED\n');

  const tests = [
    ['TEST 1: Syntax', 'python3 -m py_compile /root/coordination/arch_mapper.py && echo "PASS" || echo "FAIL"'],
    ['TEST 2: Dep Text', 'python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --dep-text /root/coordination/findings/arch_report.txt 2>&1'],
    ['TEST 3: Mermaid', 'python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --graph /root/coordination/findings/arch_diagram.md 2>&1'],
    ['TEST 4: Circular', 'python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --circular 2>&1'],
    ['TEST 5: JSON', 'python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --json /root/coordination/findings/arch_data.json 2>&1'],
    ['TEST 6: DOT', 'python3 /root/coordination/arch_mapper.py --bot-dir /root/psvibe-sales-bot --dot /root/coordination/findings/arch_graph.dot 2>&1'],
  ];

  for (const [label, cmd] of tests) {
    console.log(`--- ${label} ---`);
    const res = await execCmd(conn, cmd);
    console.log(res.out || res);
    console.log(`(exit: ${res.code})\n`);
  }
  
  // Read the JSON output for stats
  console.log('--- Reading JSON stats ---');
  const jsonRes = await execCmd(conn, 'cat /root/coordination/findings/arch_data.json');
  console.log(jsonRes.out);
  
  conn.end();
}

main().catch(e => console.error('FATAL:', e));
