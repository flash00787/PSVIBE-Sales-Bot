const { Client } = require('ssh2');
const fs = require('fs');

function execCmd(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) { reject(err); return; }
      let out = '', errOut = '';
      stream.on('data', d => { out += d.toString(); });
      stream.stderr.on('data', d => { errOut += d.toString(); });
      stream.on('close', () => {
        if (errOut) console.error('STDERR:', errOut);
        resolve(out);
      });
    });
  });
}

async function main() {
  const conn = new Client();
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({
      host: '5.223.81.16', port: 22, username: 'root',
      privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
    });
  });
  console.log('SSH connected\n');

  // Check wallet bot locations
  let out = await execCmd(conn, 'ls -la /root/psvibe-sale-bot/wallet_bot 2>/dev/null; echo "==="; ls -la /root/psvibe-wallet/ 2>/dev/null; echo "==="; ls -la /root/psvibe-sale-bot/customer_bot/ 2>/dev/null; echo "==="; ls /root/psvibe-sale-bot/');
  console.log('DIR STRUCTURE:\n' + out);

  conn.end();
}
main().catch(e => { console.error(e); process.exit(1); });
