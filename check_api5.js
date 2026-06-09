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
  // Get all route definitions from the API server
  console.log("===== POST/PUT/DELETE Routes =====");
  try {
    const r = await sshExec('grep -n "@app\.post\|@app\.put\|@app\.delete" /root/psvibe_api_server/app.py');
    console.log(r.stdout);
  } catch(e) { console.error(e); }
  
  console.log("\n===== Route handler function names =====");
  try {
    const r = await sshExec('grep -n "async def.*booking\|async def.*attendance\|async def.*console_game\|async def.*game_library\|async def.*disc_count\|async def.*console_to_setting\|async def.*console_from_setting" /root/psvibe_api_server/app.py');
    console.log(r.stdout);
  } catch(e) { console.error(e); }
}
main();
