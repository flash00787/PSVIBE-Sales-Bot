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

  // Check if there's a member rows endpoint
  let out = await execCmd(conn, 'curl -s "http://localhost:8000/api/sheets/members?api_key=JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" | head -c 300');
  console.log('=== /api/sheets/members ===');
  console.log(out);

  // Check the API server for any sheets/* endpoints  
  out = await execCmd(conn, 'grep -n "sheets/" /root/psvibe_api_server/app.py | head -20');
  console.log('=== sheets/ endpoints ===');
  console.log(out);

  // Check for member-related endpoints in the API server
  out = await execCmd(conn, 'grep -n "member_rows\|Card_Wallet\|member_sh\|get_all" /root/psvibe_api_server/sheets_client.py | head -30');
  console.log('=== sheets_client.py member ===');
  console.log(out);

  conn.end();
}
main().catch(e => { console.error(e); process.exit(1); });
