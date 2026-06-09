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
        console.log('=== KEYS ===', Object.keys(d));
        
        // Check what functions is
        const funcs = d.functions;
        console.log('\n=== functions TYPE ===', typeof funcs, Array.isArray(funcs));
        
        if (typeof funcs === 'object' && !Array.isArray(funcs)) {
          // It's an object - show its keys
          console.log('\n=== functions KEYS ===', Object.keys(funcs).slice(0, 20));
          // Show some entries
          const names = Object.keys(funcs).slice(0, 20);
          for (const name of names) {
            const f = funcs[name];
            console.log(`${name.padEnd(40)} | ${typeof f} | ${JSON.stringify(f).substring(0, 60)}`);
          }
        } else if (Array.isArray(funcs)) {
          console.log('\n=== First 20 functions ===');
          for (const f of funcs.slice(0, 20)) {
            console.log(JSON.stringify(f).substring(0, 100));
          }
        }
        
        // Check bot_commands
        const cmds = d.bot_commands;
        console.log('\n=== bot_commands TYPE ===', typeof cmds, Array.isArray(cmds));
        if (Array.isArray(cmds)) {
          for (const c of cmds.slice(0, 15)) {
            console.log(JSON.stringify(c).substring(0, 100));
          }
        }
        
        // Check summary
        console.log('\n=== SUMMARY ===', JSON.stringify(d.summary || {}, null, 2).substring(0, 500));
        
      } catch(e) {
        console.error('Parse error:', e.message);
        console.log('Raw:', o.substring(0, 1000));
      }
      conn.end();
      process.exit(0);
    });
  });
}).connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: key });
