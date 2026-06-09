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
  // Step 1: Find fetch_member_data definition in __init__.py
  console.log("===== STEP 1: Find fetch_member_data in __init__.py =====");
  try {
    const r = await sshExec(`grep -n 'def fetch_member_data\|def fetch_balance_mins\|def fetch_members_async\|def fetch_member_tier\|def fetch_member_effective_rate' /root/psvibe-sales-bot/bot/__init__.py`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 2: Read fetch_member_data function
  console.log("\n===== STEP 2: Read fetch_member_data function =====");
  try {
    const r = await sshExec(`sed -n '1,20p' /root/psvibe-sales-bot/bot/__init__.py`);
    console.log(r.stdout);
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 3: Search for fetch_member_data and surrounding context
  console.log("\n===== STEP 3: fetch_member_data around line 2000 area =====");
  try {
    const r = await sshExec(`grep -n 'fetch_member_data\|def fetch_member' /root/psvibe-sales-bot/bot/__init__.py`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 4: How many lines in __init__.py?
  console.log("\n===== STEP 4: __init__.py line count =====");
  try {
    const r = await sshExec(`wc -l /root/psvibe-sales-bot/bot/__init__.py`);
    console.log(r.stdout);
  } catch(e) { console.log("ERROR:", e.message); }
}
main().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
