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
  // Find all POST/PUT/DELETE routes
  console.log("===== POST/PUT/DELETE Routes =====");
  try {
    const r = await sshExec("grep -n 'app\.post\|app\.put\|app\.delete' /root/psvibe_api_server/app.py");
    console.log(r.stdout);
  } catch(e) { console.error(e); }
}
main();
