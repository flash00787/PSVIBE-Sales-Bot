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
  // V1 __name__ == "__main__" block
  console.log("===== V1 __name__ == __main__ =====");
  try {
    const r = await sshExec(`sed -n '12168,12300p' /root/staging/monolithic_ref/main.py`);
    console.log(r.stdout.substring(0, 6000));
  } catch(e) {}

  // V2 bot directory structure
  console.log("\n===== V2 bot/ file listing =====");
  try {
    const r = await sshExec(`ls -la /root/staging/bot_src/bot/`);
    console.log(r.stdout);
  } catch(e) {}

  // V2 bot/handlers dir
  console.log("\n===== V2 bot/handlers/ listing =====");
  try {
    const r = await sshExec(`ls -la /root/staging/bot_src/bot/handlers/ 2>/dev/null`);
    console.log(r.stdout);
  } catch(e) {}

  // V2 schema.sql - table names
  console.log("\n===== V2 schema.sql tables =====");
  try {
    const r = await sshExec(`grep -i "CREATE TABLE" /root/staging/bot_src/sqlite/schema.sql`);
    console.log(r.stdout);
  } catch(e) {}

  // V1 line count
  console.log("\n===== V1 main.py line count =====");
  try {
    const r = await sshExec(`wc -l /root/staging/monolithic_ref/main.py`);
    console.log(r.stdout);
  } catch(e) {}

  // V2 bot/__init__.py line count  
  console.log("\n===== V2 bot/__init__.py line count =====");
  try {
    const r = await sshExec(`wc -l /root/staging/bot_src/bot/__init__.py`);
    console.log(r.stdout);
  } catch(e) {}

  // V2 app.py line count
  console.log("\n===== V2 app.py line count =====");
  try {
    const r = await sshExec(`wc -l /root/staging/bot_src/bot/app.py`);
    console.log(r.stdout);
  } catch(e) {}
  
  // V2 has N8N_SESSION_WEBHOOK 
  console.log("\n===== V2 N8N references =====");
  try {
    const r = await sshExec(`grep -in "n8n\\|N8N_" /root/staging/bot_src/bot/__init__.py | head -20`);
    console.log(r.stdout);
  } catch(e) {}
}
main().catch(e => console.error(e));
