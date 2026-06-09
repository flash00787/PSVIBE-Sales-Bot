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
  // Get lines 60-200 of app.py  
  console.log("===== app.py lines 60-200 =====");
  try {
    const r = await sshExec('sed -n "60,200p" /root/psvibe_api_server/app.py');
    console.log(r.stdout);
  } catch(e) { console.error(e); }
  
  console.log("\n===== line count =====");
  try {
    const r = await sshExec('wc -l /root/psvibe_api_server/app.py');
    console.log(r.stdout);
  } catch(e) { console.error(e); }
}
main();
