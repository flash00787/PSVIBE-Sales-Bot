const { Client } = require('ssh2');
const fs = require('fs');

function sshExec(command, timeout = 60000) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let result = '';
    let err = '';
    const timer = setTimeout(() => { conn.end(); reject(new Error('Timeout')); }, timeout);
    conn.on('ready', () => {
      conn.exec(command, (e, stream) => {
        if (e) { clearTimeout(timer); conn.end(); return reject(e); }
        stream.on('data', d => result += d.toString());
        stream.stderr.on('data', d => err += d.toString());
        stream.on('close', () => {
          clearTimeout(timer);
          conn.end();
          resolve({ stdout: result, stderr: err });
        });
      });
    });
    conn.on('error', e => { clearTimeout(timer); reject(e); });
    conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
  });
}

async function main() {
  // Read fetch_member_data function in __init__.py (line 2321)
  console.log("===== fetch_member_data() in __init__.py =====");
  try {
    const r = await sshExec(`sed -n '2321,2370p' /root/psvibe-sales-bot/bot/__init__.py`);
    console.log(r.stdout.substring(0, 6000));
  } catch(e) { console.log("ERROR:", e.message); }

  // Read api_fetch_member_data in api_client.py
  console.log("\n===== api_fetch_member_data() in api_client.py =====");
  try {
    const r = await sshExec(`sed -n '230,250p' /root/psvibe-sales-bot/bot/api_client.py`);
    console.log(r.stdout.substring(0, 4000));
  } catch(e) { console.log("ERROR:", e.message); }

  // Read _api_call in api_client.py to understand the API endpoint
  console.log("\n===== _api_call in api_client.py =====");
  try {
    const r = await sshExec(`sed -n '45,140p' /root/psvibe-sales-bot/bot/api_client.py`);
    console.log(r.stdout.substring(0, 6000));
  } catch(e) { console.log("ERROR:", e.message); }

  // Check the API server for the member data endpoint
  console.log("\n===== API server: grep for /member route =====");
  try {
    const r = await sshExec(`grep -n 'member\|/member\|wallet_mins' /root/psvibe_api_server/app.py | head -40`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }
}
main().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
