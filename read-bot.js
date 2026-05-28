const { Client } = require('ssh2');
const fs = require('fs');

function execCmd(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) { reject(err); return; }
      let out = '';
      stream.on('data', d => { out += d.toString(); });
      stream.on('close', () => resolve(out));
    });
  });
}

async function main() {
  const conn = new Client();
  await new Promise(r => { conn.on('ready', r); conn.connect({host:'5.223.81.16',port:22,username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')}); });
  console.log('Connected');

  // Read key function sections: fetch_members, fetch_staff, etc.
  // Lines 1385-1700 cover the cached data section
  let out = await execCmd(conn, "sed -n '1385,1550p' /root/psvibe-sale-bot/bot/__init__.py");
  console.log('=== LINES 1385-1550 ===');
  console.log(out);

  console.log('\n=== LINES 1550-1700 ===');
  out = await execCmd(conn, "sed -n '1550,1700p' /root/psvibe-sale-bot/bot/__init__.py");
  console.log(out);

  console.log('\n=== LINES 1700-1900 ===');
  out = await execCmd(conn, "sed -n '1700,1900p' /root/psvibe-sale-bot/bot/__init__.py");
  console.log(out);

  conn.end();
}
main().catch(e => { console.error(e); process.exit(1); });
