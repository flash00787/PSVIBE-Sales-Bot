const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

conn.on('ready', () => {
  conn.exec('cat /root/agent_output/function_map.json', (err, stream) => {
    if (err) { console.error(err); process.exit(1); }
    let o = '';
    stream.on('data', d => o += d.toString());
    stream.stderr.on('data', d => o += d.toString());
    stream.on('close', () => {
      try {
        const d = JSON.parse(o);
        const funcs = d.functions || [];
        console.log('=== KEYS ===', Object.keys(d));
        
        // Show API-relevant functions
        const apiFuncs = funcs.filter(f => f.type === 'api' || f.type === 'command' || f.type === 'query' || f.type === 'db');
        console.log('\n=== API/DATABASE FUNCTIONS (first 30) ===');
        for (const f of (apiFuncs.length > 0 ? apiFuncs : funcs).slice(0, 30)) {
          if (typeof f === 'object') {
            const n = (f.name || '?').padEnd(35);
            const fl = (f.file || '').padEnd(25);
            const t = (f.type || '').padEnd(10);
            const p = JSON.stringify(f.params || '') || '';
            console.log(`${n} | ${fl} | ${t} | ${p.substring(0, 40)}`);
          }
        }
        console.log(`\nTotal functions: ${funcs.length}`);
        console.log(`API-relevant: ${apiFuncs.length}`);
      } catch(e) {
        console.error('Parse error:', e.message);
        console.log('Raw output (first 500 chars):', o.substring(0, 500));
      }
      conn.end();
      process.exit(0);
    });
  });
}).connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: key });
