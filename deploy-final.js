const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const PRIVATE_KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

async function main() {
  const conn = new Client();
  await new Promise((res, rej) => {
    conn.on('ready', res);
    conn.on('error', rej);
    conn.connect({ host: HOST, port: 22, username: 'root', privateKey: PRIVATE_KEY, readyTimeout: 30000 });
  });
  console.log('SSH connected');

  const execOk = (cmd) => new Promise((res) => {
    conn.exec(cmd, (err, stream) => {
      if (err) { console.error('err:', err); res(''); return; }
      let out = '';
      stream.on('data', d => { out += d.toString(); process.stdout.write(d.toString()); });
      stream.stderr.on('data', d => { out += d.toString(); });
      stream.on('close', () => res(out));
    });
  });

  // Final status verification
  console.log('\n========== FINAL STATUS ==========');
  await execOk('echo "--- Service Status ---" && systemctl status psvibe-bot.service --no-pager -l | head -15');
  await execOk('echo "--- Enabled? ---" && systemctl is-enabled psvibe-bot.service');
  await execOk('echo "--- Latest Logs ---" && journalctl -u psvibe-bot.service --no-pager -n 10 --since "1 minute ago"');
  await execOk('echo "--- API Service ---" && systemctl is-active psvibe-api.service');
  await execOk('echo "--- Caddy ---" && systemctl is-active caddy');
  await execOk('echo "--- Process Tree ---" && ps aux | grep -E "python3.*main|psvibe" | grep -v grep');
  await execOk('echo "--- File Count ---" && find /root/Sales-Tele-Bot_refactored -type f | wc -l');

  conn.end();
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
