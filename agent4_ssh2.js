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

        // Find all Python files in V1
        results.v1_files = await execCommand("find /root/psvibe-sale-bot -name '*.py' -type f | sort");

        // Check bot.py for sheet references
        results.v1_bot = await execCommand("ls -la /root/psvibe-sale-bot/bot.py && wc -l /root/psvibe-sale-bot/bot.py");

        // Grep bot.py for sheet names
        results.v1_bot_sheets = await execCommand(
          "grep -n 'worksheet\\|gspread\\|sheet\\|spreadsheet\\|Card_Wallet\\|TopUp_Log\\|Sales_Daily\\|Console_Booking\\|Stock\\|Ledger\\|Wallet\\|TopUp' /root/psvibe-sale-bot/bot.py | head -40"
        );

        // Grep all files for sheet tab names
        results.v1_all_tabs = await execCommand(
          "grep -rn 'worksheets\\|Card_Wallet\\|TopUp_Log\\|Sales_Daily\\|Console_Booking\\|Stock\\|Ledger\\|Wallet' /root/psvibe-sale-bot/ | head -40"
        );

        // Check for service account JSON
        results.v1_service_account = await execCommand(
          "find /root/psvibe-sale-bot -name '*.json' -type f 2>/dev/null"
        );

        // Check the V2 backup tarball
        results.v2_tar = await execCommand(
          "tar tzf /root/backups/psvibe-v2-running_20260527_2102.tar.gz 2>/dev/null | head -60"
        );

        // Extract V2 backup
        results.v2_extract = await execCommand(
          "rm -rf /tmp/v2_check2 && mkdir -p /tmp/v2_check2 && tar xzf /root/backups/psvibe-v2-running_20260527_2102.tar.gz -C /tmp/v2_check2 2>&1"
        );

        // Find Python files in V2
        results.v2_pyfiles = await execCommand(
          "find /tmp/v2_check2 -name '*.py' -type f | sort"
        );

        // Search V2 for sheet references
        results.v2_sheets = await execCommand(
          "grep -rn 'Card_Wallet\\|TopUp_Log\\|Sales_Daily\\|Console_Booking\\|Stock\\|Ledger\\|Wallet\\|worksheet\\|gspread\\|spreadsheet' /tmp/v2_check2/ 2>/dev/null | head -50"
        );

        // Check if V2 has API client
        results.v2_api = await execCommand(
          "find /tmp/v2_check2 -name '*api*' -o -name '*client*' | head -20"
        );

        // Check V2 service account
        results.v2_json = await execCommand(
          "find /tmp/v2_check2 -name '*.json' -type f 2>/dev/null | head -10"
        );

        // Docker containers
        results.containers = await execCommand("docker ps -a --format '{{.Names}} {{.Image}} {{.Status}}' 2>/dev/null");

        // Check MySQL databases/tables related to bot
        results.mysql_db = await execCommand(
          "docker exec psvibe-mysql mysql -uroot -p'psvibe_root_2024' -e 'SHOW DATABASES;' 2>/dev/null"
        );

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
