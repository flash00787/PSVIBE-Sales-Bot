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
  // Just get the whole file
  console.log("===== Fetching API server app.py =====");
  try {
    const r = await sshExec('cat /root/psvibe_api_server/app.py');
    fs.writeFileSync('/home/node/.openclaw/workspace/api_server_app.py', r.stdout);
    console.log(`Saved (${r.stdout.length} bytes)`);
  } catch(e) { console.error(e); }
}
main();
