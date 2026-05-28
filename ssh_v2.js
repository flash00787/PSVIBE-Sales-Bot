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
    conn.connect({ host: '167.71.196.120', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
  });
}

async function main() {
  // Step 4: V2 bot_src structure
  console.log("===== STEP 4a: V2 bot/__init__.py exports =====");
  try {
    const r4a = await sshExec(`head -80 /root/staging/bot_src/bot/__init__.py`);
    console.log(r4a.stdout.substring(0, 8000));
    if (r4a.stderr) console.log("STDERR:", r4a.stderr);
  } catch(e) { console.log("Err:", e.message); }

  console.log("\n===== STEP 4b: V2 bot/app.py =====");
  try {
    const r4b = await sshExec(`head -120 /root/staging/bot_src/bot/app.py`);
    console.log(r4b.stdout.substring(0, 8000));
    if (r4b.stderr) console.log("STDERR:", r4b.stderr);
  } catch(e) {}

  // Step 5: Sqlite DB
  console.log("\n===== STEP 5a: V2 sqlite dir =====");
  try {
    const r5a = await sshExec(`ls -laR /root/staging/bot_src/sqlite/ 2>/dev/null || echo "NO SQLITE DIR"`);
    console.log(r5a.stdout);
  } catch(e) {}

  console.log("\n===== STEP 5b: db_manager.py =====");
  try {
    const r5b = await sshExec(`head -100 /root/staging/bot_src/sqlite/db_manager.py`);
    console.log(r5b.stdout.substring(0, 5000));
  } catch(e) {}

  console.log("\n===== STEP 5c: setup.py =====");
  try {
    const r5c = await sshExec(`head -100 /root/staging/bot_src/sqlite/setup.py`);
    console.log(r5c.stdout.substring(0, 5000));
  } catch(e) {}

  // Step 6: api_server.js
  console.log("\n===== STEP 6: api_server.js Replit/API refs =====");
  try {
    const r6 = await sshExec(`grep -in "replit\\|external\\|fetch\\|request\\|axios\\|express\\|listen" /root/Sales-Tele-Bot/api_server/api_server.js 2>/dev/null | head -40`);
    console.log(r6.stdout);
    if (r6.stderr) console.log("STDERR:", r6.stderr);
  } catch(e) {}

  // Additional: check V2 main.py
  console.log("\n===== EXTRA: V2 main.py =====");
  try {
    const re = await sshExec(`head -80 /root/staging/bot_src/main.py 2>/dev/null || head -80 /root/Sales-Tele-Bot/main.py 2>/dev/null || echo "NOT FOUND"`);
    console.log(re.stdout.substring(0, 5000));
  } catch(e) {}
}
main().catch(e => console.error(e));
