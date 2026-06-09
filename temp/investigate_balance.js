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
  // Step 1: Find "Check Member" related handlers
  console.log("===== STEP 1: Search Check Member handlers =====");
  try {
    const r = await sshExec(`grep -rn 'check.member\|check_member\|member_balance\|wallet_mins\|get_balance\|view_member\|member_info\|card_wallet' /root/psvibe-sales-bot/bot/ --include='*.py' --exclude-dir='__pycache__' | head -60`);
    console.log(r.stdout || "(no matches)");
    console.log("STDERR:", r.stderr || "(none)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 2: Search for wallet/balance display patterns  
  console.log("\n===== STEP 2: Search balance/wallet display patterns =====");
  try {
    const r = await sshExec(`grep -rn 'wallet\|balance\|column.*8\|col8\|row\[7\]\|wallet_mins\|wallet_amount\|remaining' /root/psvibe-sales-bot/bot/ --include='*.py' --exclude-dir='__pycache__' | grep -i 'balance\|member\|wallet\|card' | head -60`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 3: List bot directory structure
  console.log("\n===== STEP 3: Bot directory structure =====");
  try {
    const r = await sshExec(`ls -la /root/psvibe-sales-bot/bot/`);
    console.log(r.stdout);
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 4: List handlers directory
  console.log("\n===== STEP 4: Handlers directory =====");
  try {
    const r = await sshExec(`ls -la /root/psvibe-sales-bot/bot/handlers/`);
    console.log(r.stdout);
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 5: Check API server for member balance endpoints
  console.log("\n===== STEP 5: API server member balance endpoints =====");
  try {
    const r = await sshExec(`grep -rn 'member\|balance\|wallet\|member_balance\|get_balance\|card_wallet' /root/psvibe_api_server/ --include='*.py' --exclude-dir='__pycache__' | head -40`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 6: Check MySQL schema for member_wallets
  console.log("\n===== STEP 6: MySQL member_wallets schema =====");
  try {
    const r = await sshExec(`mysql -e "SHOW CREATE TABLE psvibe_db.member_wallets\\G" 2>/dev/null || mysql -e "SHOW TABLES LIKE '%wallet%'" 2>/dev/null`);
    console.log(r.stdout || "(no output)");
  } catch(e) { console.log("ERROR:", e.message); }

  // Step 7: Journal logs
  console.log("\n===== STEP 7: Journal logs for balance errors =====");
  try {
    const r = await sshExec(`journalctl -u psvibe-sale-bot -u psvibe-api --since "2 hours ago" -n 200 --no-pager 2>/dev/null | grep -i 'balance\|wallet\|member\|card_wallet\|column.*8\|row\[7\]' | tail -30`);
    console.log(r.stdout || "(no matches)");
  } catch(e) { console.log("ERROR:", e.message); }
}
main().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
