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
  // Step 1: Direct grep on members.py for "balance" (case insensitive)
  console.log("===== STEP 1: grep -in balance members.py =====");
  try {
    const r = await sshExec(`grep -in 'balance' /root/psvibe-sales-bot/bot/handlers/members.py | head -40`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 2: grep for wallet in members.py
  console.log("\n===== STEP 2: grep -in wallet members.py =====");
  try {
    const r = await sshExec(`grep -in 'wallet' /root/psvibe-sales-bot/bot/handlers/members.py | head -40`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 3: grep for card_wallet in all files
  console.log("\n===== STEP 3: grep -rn card_wallet =====");
  try {
    const r = await sshExec(`grep -rn 'card_wallet\|Card_wallet' /root/psvibe-sales-bot/bot/ --include='*.py' | head -40`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 4: Try looking at members.py line count and some key areas
  console.log("\n===== STEP 4: members.py line count =====");
  try {
    const r = await sshExec(`wc -l /root/psvibe-sales-bot/bot/handlers/members.py`);
    console.log(r.stdout);
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 5: Read first 100 lines of members.py to understand structure
  console.log("\n===== STEP 5: members.py first 100 lines =====");
  try {
    const r = await sshExec(`head -100 /root/psvibe-sales-bot/bot/handlers/members.py`);
    console.log(r.stdout.substring(0, 6000));
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 6: Search for "member" keyword broadly in members.py  
  console.log("\n===== STEP 6: grep -n 'member' members.py (case-insensitive, unique) =====");
  try {
    const r = await sshExec(`grep -in 'member' /root/psvibe-sales-bot/bot/handlers/members.py | head -80`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 7: Check if API server uses MySQL or GSheet for balance
  console.log("\n===== STEP 7: Check API server app.py for member endpoints =====");
  try {
    const r = await sshExec(`grep -n '@app\.route.*member\|def.*member\|member_wallet\|card_wallet\|balance' /root/psvibe_api_server/app.py | head -40`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 8: Journalctl with broader search
  console.log("\n===== STEP 8: Journalctl recent entries =====");
  try {
    const r = await sshExec(`journalctl -u psvibe-sale-bot --since '30 minutes ago' -n 100 --no-pager 2>/dev/null | tail -30`);
    console.log(r.stdout || "(no entries)");
  } catch(e) { console.log("ERROR:", e.message); }
}

main().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
