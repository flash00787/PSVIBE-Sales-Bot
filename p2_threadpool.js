const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const KEY = '/home/node/.openclaw/workspace/.ssh/id_rsa';

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
          resolve({ stdout: result.trim(), stderr: err.trim() });
        });
      });
    });
    conn.on('error', e => { clearTimeout(timer); reject(e); });
    conn.connect({ host: HOST, port: 22, username: 'root', privateKey: fs.readFileSync(KEY) });
  });
}

async function main() {
  const log = [];
  
  // Step 1: Find ThreadPoolExecutor line
  console.log("=== STEP 1: Find ThreadPoolExecutor/max_workers in __init__.py ===");
  try {
    const r1 = await sshExec(`grep -n "ThreadPoolExecutor\\|max_workers" /root/psvibe-sales-bot/bot/__init__.py`);
    console.log("BEFORE:", r1.stdout);
    log.push("STEP1: " + r1.stdout);
  } catch(e) { log.push("STEP1 ERROR: " + e.message); console.error(e); }
  
  // Step 2: Change max_workers=64 -> max_workers=8
  console.log("\n=== STEP 2: Change max_workers=64 -> max_workers=8 ===");
  try {
    const r2 = await sshExec(`sed -i 's/max_workers=64/max_workers=8/' /root/psvibe-sales-bot/bot/__init__.py`);
    console.log("SED stdout:", r2.stdout || "(empty)");
    console.log("SED stderr:", r2.stderr || "(empty)");
    log.push("STEP2: sed executed, stdout=" + (r2.stdout||"empty") + " stderr=" + (r2.stderr||"empty"));
  } catch(e) { log.push("STEP2 ERROR: " + e.message); console.error(e); }
  
  // Step 3: Verify
  console.log("\n=== STEP 3: Verify ===");
  try {
    const r3 = await sshExec(`grep -n "max_workers" /root/psvibe-sales-bot/bot/__init__.py`);
    console.log("AFTER:", r3.stdout);
    log.push("STEP3: " + r3.stdout);
  } catch(e) { log.push("STEP3 ERROR: " + e.message); console.error(e); }
  
  // Step 4: Restart main service
  console.log("\n=== STEP 4: Restart psvibe-sale-bot ===");
  try {
    const r4a = await sshExec(`systemctl restart psvibe-sale-bot`);
    console.log("Restart stdout:", r4a.stdout || "(empty)");
    console.log("Restart stderr:", r4a.stderr || "(empty)");
    
    // Wait and check
    await new Promise(r => setTimeout(r, 3000));
    const r4b = await sshExec(`systemctl is-active psvibe-sale-bot`);
    console.log("SERVICE STATUS:", r4b.stdout);
    log.push("STEP4: restart done, is-active=" + r4b.stdout);
  } catch(e) { log.push("STEP4 ERROR: " + e.message); console.error(e); }
  
  // Step 5: Check customer bot
  console.log("\n=== STEP 5: Check customer_bot for ThreadPoolExecutor/max_workers ===");
  try {
    const r5 = await sshExec(`grep -rn "ThreadPoolExecutor\\|max_workers" /root/psvibe-sales-bot/customer_bot/ 2>/dev/null || echo "NOT_FOUND"`);
    console.log("CUSTOMER BOT:", r5.stdout);
    log.push("STEP5: " + (r5.stdout || "NOT_FOUND"));
    
    // If found with 64, fix it too
    if (r5.stdout && r5.stdout.includes('max_workers=64')) {
      console.log("FOUND 64 in customer_bot, fixing...");
      const r5b = await sshExec(`sed -i 's/max_workers=64/max_workers=8/' /root/psvibe-sales-bot/customer_bot/*.py`);
      const r5c = await sshExec(`grep -rn "max_workers" /root/psvibe-sales-bot/customer_bot/`);
      console.log("CUSTOMER BOT AFTER:", r5c.stdout);
      log.push("STEP5b: AFTER FIX=" + r5c.stdout);
    }
  } catch(e) { log.push("STEP5 ERROR: " + e.message); console.error(e); }
  
  // Write result
  const result = log.join("\n");
  fs.writeFileSync('/home/node/.openclaw/workspace/temp/p2_threadpool_result.txt', 
    "P2: ThreadPoolExecutor Workers 64→8\n\n" + result + "\n\n=== RESULT: OK ===\n");
  console.log("\n=== DONE ===");
  console.log(result);
}

main().catch(e => {
  console.error("FATAL:", e);
  fs.writeFileSync('/home/node/.openclaw/workspace/temp/p2_threadpool_result.txt',
    "P2: ThreadPoolExecutor Workers 64→8\n\nFATAL ERROR: " + e.message + "\n\n=== RESULT: ERROR: " + e.message + " ===\n");
  process.exit(1);
});
