const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');

const conn = new Client();

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

function execCommand(cmd, timeout = 15000) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, { timeout }, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', (data) => { stdout += data.toString(); });
      stream.stderr.on('data', (data) => { stderr += data.toString(); });
      stream.on('close', (code) => {
        resolve({ stdout: stdout.trim(), stderr: stderr.trim(), code });
      });
    });
  });
}

async function runAll() {
  return new Promise((resolve, reject) => {
    conn.on('ready', async () => {
      try {
        const results = {};

        // Step 1a
        results.step1a = await execCommand(
          "grep -rn 'gspread\\|client\\|sheet\\|worksheet\\|spreadsheet' /root/psvibe-sale-bot/main.py | head -30"
        );

        // Step 1b
        results.step1b = await execCommand(
          "grep -rn 'GC_KEY\\|SERVICE_ACCOUNT\\|creds\\|credentials' /root/psvibe-sale-bot/main.py | head -10"
        );

        // Step 1c
        results.step1c = await execCommand(
          "grep -rn 'Card_Wallet\\|TopUp_Log\\|Sales_Daily\\|Console_Booking\\|Stock' /root/psvibe-sale-bot/main.py | head -30"
        );

        // Step 2a
        results.step2a = await execCommand(
          "tar tzf /root/backups/psvibe-refactored_20260526_233759.tar.gz 2>/dev/null | head -50"
        );

        // Step 2b
        results.step2b = await execCommand(
          "mkdir -p /tmp/v2_check && tar xzf /root/backups/psvibe-refactored_20260526_233759.tar.gz -C /tmp/v2_check 2>&1"
        );

        // Step 2c
        results.step2c = await execCommand(
          "find /tmp/v2_check -name '*.py' -exec grep -l 'Card_Wallet\\|TopUp_Log\\|Sales_Daily' {} \\;"
        );

        // Step 2d
        results.step2d = await execCommand(
          "grep -rn 'Card_Wallet\\|TopUp_Log\\|Sales_Daily\\|Console_Booking\\|Stock' /tmp/v2_check/ 2>/dev/null | head -40"
        );

        // Step 3a
        results.step3a = await execCommand("docker ps -a 2>/dev/null | grep mysql");

        // Step 3b
        results.step3b = await execCommand("docker ps -a 2>/dev/null | grep sync");

        // Step 3c
        results.step3c = await execCommand(
          "cat /root/psvibe-sale-bot/api_client.py 2>/dev/null | head -30"
        );

        results.backups_ls = await execCommand("ls -la /root/backups/ 2>/dev/null | head -20");

        conn.end();
        resolve(results);
      } catch (e) {
        conn.end();
        reject(e);
      }
    });
    conn.on('error', reject);
    conn.connect({ host: HOST, username: USER, privateKey: KEY });
  });
}

runAll().then(results => {
  for (const [key, val] of Object.entries(results)) {
    console.log(`\n===== ${key} =====`);
    console.log(val.stdout || '(empty)');
    if (val.stderr) console.log('STDERR:', val.stderr);
    if (val.code !== 0 && val.code !== null) console.log('Exit:', val.code);
  }
}).catch(err => {
  console.error('CONNECTION ERROR:', err.message);
  process.exit(1);
});
