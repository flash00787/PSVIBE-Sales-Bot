const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();

conn.on('ready', () => {
  const results = {};
  let done = 0;
  
  const cmds = {
    extra_bot: 'ps aux | grep -E "8545665013|psvibe.*main" | grep -v grep',
    customer_log: 'journalctl -u psvibe_customer_bot --since "5 min ago" --no-pager 2>/dev/null | grep -i "conflict\\|error\\|CRITICAL" | grep -v "429\\|500" | tail -5',
  };
  
  Object.entries(cmds).forEach(([k, cmd]) => {
    conn.exec(cmd, (err, stream) => {
      if (err) { results[k] = `ERR: ${err.message}`; done++; checkFinish(); return; }
      let out = '';
      stream.on('data', d => out += d.toString());
      stream.stderr.on('data', d => out += d.toString());
      stream.on('close', () => { results[k] = out.trim(); done++; checkFinish(); });
    });
  });
  
  function checkFinish() {
    if (done === 2) {
      Object.entries(results).forEach(([k,v]) => console.log(`--- ${k} ---\n${v}\n`));
      conn.end();
    }
  }
});

conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'), readyTimeout: 10000 });
