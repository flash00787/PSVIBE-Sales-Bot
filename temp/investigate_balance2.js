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
  // Step 1: Search broadly in members.py for balance/wallet/check member
  console.log("===== STEP 1: Search members.py for balance/check member =====");
  try {
    const r = await sshExec(`grep -n 'balance\|wallet\|check.*member\|view.*member\|member.*info\|card_wallet\|wallet_mins\|column\[8\]\|col8\|row\[7\]' /root/psvibe-sales-bot/bot/handlers/members.py | head -80`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 2: Search finance.py for balance
  console.log("\n===== STEP 2: Search finance.py for balance =====");
  try {
    const r = await sshExec(`grep -n 'balance\|wallet\|card_wallet' /root/psvibe-sales-bot/bot/handlers/finance.py | head -60`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 3: Check app.py for member check routes
  console.log("\n===== STEP 3: Search app.py for member check =====");
  try {
    const r = await sshExec(`grep -n 'check_member\|member_balance\|show_member\|view_member\|balance' /root/psvibe-sales-bot/bot/app.py | head -40`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 4: Check __init__.py for member check
  console.log("\n===== STEP 4: Search __init__.py for member check =====");
  try {
    const r = await sshExec(`grep -n 'check_member\|member_balance\|show_member\|view_member' /root/psvibe-sales-bot/bot/__init__.py | head -40`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 5: Search API files more broadly
  console.log("\n===== STEP 5: API server directory listing =====");
  try {
    const r = await sshExec(`ls -la /root/psvibe_api_server/`);
    console.log(r.stdout);
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 6: Search API server for balance/member
  console.log("\n===== STEP 6: Search API for balance/wallet =====");
  try {
    const r = await sshExec(`grep -rn 'balance\|wallet\|member\|card_wallet' /root/psvibe_api_server/ --include='*.py' | head -50`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 7: Check MySQL tables
  console.log("\n===== STEP 7: MySQL tables =====");
  try {
    const r = await sshExec(`mysql -e "SHOW TABLES FROM psvibe_db" 2>/dev/null`);
    console.log(r.stdout || "(no output)");
  } catch(e) { console.log("ERROR:", e.message); }
}

main().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
