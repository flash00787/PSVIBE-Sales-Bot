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
  // Step 2: Find ALL Replit & API references
  console.log("===== STEP 2: Replit & API references =====");
  try {
    const r2 = await sshExec(`grep -in "replit\\|API_BASE_URL\\|keep_alive\\|webhook\\|requests\\.\\(get\\|post\\)\\|urllib\\|aiohttp" /root/staging/monolithic_ref/main.py | head -60`);
    console.log("STDOUT:", r2.stdout);
    if (r2.stderr) console.log("STDERR:", r2.stderr);
  } catch(e) { console.log("Error step2:", e.message); }

  // Step 3: Read key sections of V1 main.py
  console.log("\n===== STEP 3a: Search for main() and Application =====");
  try {
    const r3a = await sshExec(`grep -in "def main\\|Application.builder\\|ConversationHandler\\|if __name__" /root/staging/monolithic_ref/main.py | head -20`);
    console.log("STDOUT:", r3a.stdout);
  } catch(e) {}
  
  console.log("\n===== STEP 3b: API functions around 1400-1450 =====");
  try {
    const r3b = await sshExec(`sed -n '1380,1550p' /root/staging/monolithic_ref/main.py`);
    console.log(r3b.stdout.substring(0, 8000));
  } catch(e) {}

  console.log("\n===== STEP 3c: Google Sheets references =====");
  try {
    const r3c = await sshExec(`grep -in "Card_Wallet\\|Sales_Daily\\|sheet\\|worksheet\\|gsheet\\|spreadsheet" /root/staging/monolithic_ref/main.py | head -40`);
    console.log("STDOUT:", r3c.stdout);
  } catch(e) {}

  console.log("\n===== STEP 3d: ConversationHandler definitions =====");
  try {
    const r3d = await sshExec(`grep -in "ConversationHandler\\|States\\|states=" /root/staging/monolithic_ref/main.py | head -30`);
    console.log("STDOUT:", r3d.stdout);
  } catch(e) {}
}
main().catch(e => console.error(e));
