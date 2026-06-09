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
  // Search entire bot directory for fetch_member_data definition
  console.log("===== STEP 1: Search everywhere for fetch_member_data definition =====");
  try {
    const r = await sshExec(`grep -rn 'def fetch_member_data' /root/psvibe-sales-bot/ --include='*.py' | head -20`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Search for fetch_member_data usage
  console.log("\n===== STEP 2: Search everywhere for fetch_member_data =====");
  try {
    const r = await sshExec(`grep -rn 'fetch_member_data' /root/psvibe-sales-bot/bot/ --include='*.py' | head -20`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Search for wallet_mins in __init__.py
  console.log("\n===== STEP 3: Search wallet_mins in __init__.py =====");
  try {
    const r = await sshExec(`grep -n 'wallet_mins\|card_wallet\|fetch_balance\|member_sh' /root/psvibe-sales-bot/bot/__init__.py | head -40`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Check what api_client.py provides
  console.log("\n===== STEP 4: api_client.py functions =====");
  try {
    const r = await sshExec(`grep -n 'def ' /root/psvibe-sales-bot/bot/api_client.py | head -30`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Check __init__.py around lines with 'fetch' 
  console.log("\n===== STEP 5: Lines near 'fetch' in __init__.py =====");
  try {
    const r = await sshExec(`grep -n 'fetch_member\|fetch_balance\|fetch.*member' /root/psvibe-sales-bot/bot/__init__.py | head -30`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }
}

main().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
