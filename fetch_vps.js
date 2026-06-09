const { Client } = require('ssh2');
const fs = require('fs');

function sshExec(command, timeout = 30000) {
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
  // Get api_client.py
  console.log("===== api_client.py =====");
  try {
    const r = await sshExec('cat /root/psvibe-sale-bot/bot/api_client.py');
    fs.writeFileSync('/home/node/.openclaw/workspace/vps_api_client.py', r.stdout);
    console.log(`Saved vps_api_client.py (${r.stdout.length} bytes)`);
  } catch(e) { console.error(e); }

  // Get current __init__.py
  console.log("\n===== __init__.py =====");
  try {
    const r = await sshExec('cat /root/psvibe-sale-bot/bot/__init__.py');
    fs.writeFileSync('/home/node/.openclaw/workspace/vps_init.py', r.stdout);
    console.log(`Saved vps_init.py (${r.stdout.length} bytes)`);
  } catch(e) { console.error(e); }
}
main();
