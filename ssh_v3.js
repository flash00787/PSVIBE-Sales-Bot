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
  // V1 ConversationHandler states (full block around line 11767)
  console.log("===== V1 CONVERSATION HANDLER FULL =====");
  try {
    const r = await sshExec(`sed -n '11760,12100p' /root/staging/monolithic_ref/main.py`);
    console.log(r.stdout.substring(0, 12000));
  } catch(e) {}

  // V1 _replit_get, _replit_post, _replit_patch functions
  console.log("\n===== V1 _replit_get/post/patch =====");
  try {
    const r = await sshExec(`sed -n '8300,8400p' /root/staging/monolithic_ref/main.py`);
    console.log(r.stdout.substring(0, 8000));
  } catch(e) {}

  // V1 keep_alive references
  console.log("\n===== V1 keep_alive usages =====");
  try {
    const r = await sshExec(`grep -n "keep_alive" /root/staging/monolithic_ref/main.py`);
    console.log(r.stdout);
  } catch(e) {}

  // V1 main() function
  console.log("\n===== V1 main() =====");
  try {
    const r = await sshExec(`sed -n '11767,12168p' /root/staging/monolithic_ref/main.py`);
    console.log(r.stdout.substring(0, 10000));
  } catch(e) {}
  
  // V2 bot/__init__.py lines 80-200
  console.log("\n===== V2 bot/__init__.py 80-200 =====");
  try {
    const r = await sshExec(`sed -n '80,200p' /root/staging/bot_src/bot/__init__.py`);
    console.log(r.stdout.substring(0, 8000));
  } catch(e) {}

  // V1 STAT variable definitions (around line 542)
  console.log("\n===== V1 STATE definitions =====");
  try {
    const r = await sshExec(`sed -n '540,820p' /root/staging/monolithic_ref/main.py`);
    console.log(r.stdout.substring(0, 8000));
  } catch(e) {}
}
main().catch(e => console.error(e));
