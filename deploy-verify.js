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
    console.log(`\n>>> ${cmd.slice(0, 120)}`);
    conn.exec(cmd, (err, stream) => {
      if (err) { console.error('err:', err); res(''); return; }
      let out = '';
      stream.on('data', d => { out += d.toString(); process.stdout.write(d.toString()); });
      stream.stderr.on('data', d => { process.stderr.write(d.toString()); out += d.toString(); });
      stream.on('close', () => res(out));
    });
  });

  // Wait a few seconds then check logs
  await new Promise(r => setTimeout(r, 5000));
  await execOk('journalctl -u psvibe-bot.service --no-pager -n 50 --since "1 minute ago"');
  
  // Check if it's still running
  await execOk('systemctl is-active psvibe-bot.service');
  
  // Check the bot_status.log
  await execOk('tail -30 /root/Sales-Tele-Bot_refactored/bot_status.log');

  conn.end();
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
