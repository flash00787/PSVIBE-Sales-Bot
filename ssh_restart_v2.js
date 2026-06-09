const { Client } = require('ssh2');
const fs = require('fs');

async function sshExec(conn, cmd, timeoutMs = 15000) {
  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve({ code: -1, out: '', err: 'TIMEOUT' }), timeoutMs);
    conn.exec(cmd, (err, stream) => {
      let out = '', errOut = '';
      if (err) { clearTimeout(timer); resolve({ code: -2, out: '', err: err.message }); return; }
      stream.on('data', (d) => out += d.toString());
      stream.stderr.on('data', (d) => errOut += d.toString());
      stream.on('close', (code) => { clearTimeout(timer); resolve({ code, out, err: errOut }); });
    });
  });
}

const conn = new Client();
let results = [];

conn.on('ready', async () => {
  console.log('SSH connected');

  // Restart
  let r1 = await sshExec(conn, 'systemctl restart psvibe_customer_bot.service 2>&1; echo EXIT:$?', 20000);
  results.push({ step: 'restart', ...r1 });
  console.log('Restart:', r1.code, r1.out.slice(0, 100));

  // Sleep 3 then check status
  let r2 = await sshExec(conn, 'sleep 3 && systemctl is-active psvibe_customer_bot.service 2>&1; echo EXIT:$?', 20000);
  results.push({ step: 'status', ...r2 });
  console.log('Status:', r2.out.trim());

  // Journal
  let r3 = await sshExec(conn, 'journalctl -u psvibe_customer_bot.service --since "2 min ago" --no-pager -n 30 2>&1; echo EXIT:$?', 15000);
  results.push({ step: 'journal', ...r3 });
  console.log('Journal lines:', (r3.out.match(/\n/g) || []).length);

  fs.writeFileSync('/home/node/.openclaw/workspace/temp/restart_results_v2.json', JSON.stringify(results, null, 2));
  console.log('DONE');
  conn.end();
});

conn.on('error', (err) => { console.error('SSH error:', err); process.exit(1); });
conn.connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
