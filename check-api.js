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

  const KEY = 'JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ';
  const BASE = 'http://localhost:8000';

  // Check various endpoints
  const endpoints = [
    '/api/fetch_console_status',
    '/api/fetch_staff',
    '/api/fetch_base_rate',
    '/api/fetch_games',
    '/api/fetch_allowed_staff_ids',
    '/api/next_voucher',
    '/api/fetch_new_member_defaults',
    '/api/fetch_member_data/PSV_A_000',
  ];

  for (const ep of endpoints) {
    console.log(`\n=== ${ep} ===`);
    const resp = await execCmd(conn, `curl -s "${BASE}${ep}?api_key=${KEY}" | head -c 500`);
    console.log(resp);
  }

  conn.end();
}
main().catch(e => { console.error(e); process.exit(1); });
