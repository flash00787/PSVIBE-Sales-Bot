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

        // MySQL: try user login
        results.mysql_user = await execCommand(
          "docker exec psvibe-mysql mysql -upsvibe_user -p'PsVibe@User2024!' -e 'SHOW DATABASES; SHOW TABLES FROM psvibe_api;' 2>&1"
        );

        // MySQL root with correct pswd
        results.mysql_root2 = await execCommand(
          "docker exec psvibe-mysql mysql -uroot -p'PsVibe@MySQL2024!' -e 'SHOW DATABASES; SHOW TABLES FROM psvibe_api;' 2>&1"
        );

        // V1 gspread connection init (continue bot/__init__.py)
        results.v1_init2 = await execCommand(
          "sed -n '100,200p' /root/psvibe-sale-bot/bot/__init__.py"
        );

        // V2 gspread connection init
        results.v2_init2 = await execCommand(
          "sed -n '100,200p' /tmp/v2_check2/Sales-Tele-Bot_refactored/bot/__init__.py"
        );

        // Check if V2 also has api_client.py (in the backup)
        results.v2_has_apiclient = await execCommand(
          "find /tmp/v2_check2 -name 'api_client.py' -type f 2>/dev/null"
        );

        // Check V1's api_client usage across handlers
        results.v1_api_usage = await execCommand(
          "grep -rn 'api_client\\|from bot.api_client\\|from api_client' /root/psvibe-sale-bot/bot/ 2>/dev/null | grep -v __pycache__ | head -20"
        );

        // Check the running V2 at /root/Sales-Tele-Bot_refactored (if exists)
        results.v2_running = await execCommand(
          "ls -la /root/Sales-Tele-Bot_refactored/bot/__init__.py 2>/dev/null && wc -l /root/Sales-Tele-Bot_refactored/bot/__init__.py 2>/dev/null"
        );

        // V2 running init.py head
        results.v2_running_init = await execCommand(
          "sed -n '1,60p' /root/Sales-Tele-Bot_refactored/bot/__init__.py 2>/dev/null"
        );

        // V2 running - check for api_client import
        results.v2_running_api = await execCommand(
          "grep -n 'api_client' /root/Sales-Tele-Bot_refactored/bot/__init__.py 2>/dev/null | head -10"
        );

        // Check what spreadsheet ID is used
        results.sheet_id = await execCommand(
          "grep -rn 'SHEET_ID\\|SPREADSHEET_ID' /root/psvibe-sale-bot/bot/__init__.py | head -10"
        );

        // V1 sheet connection details
        results.v1_sheet_connect = await execCommand(
          "grep -n 'open_by_key\\|gc\\.open\\|authorize\\|ServiceAccountCredentials\\|spreadsheet' /root/psvibe-sale-bot/bot/__init__.py | head -20"
        );

        // V2 sheet connection details
        results.v2_sheet_connect = await execCommand(
          "grep -n 'open_by_key\\|gc\\.open\\|authorize\\|ServiceAccountCredentials\\|spreadsheet' /tmp/v2_check2/Sales-Tele-Bot_refactored/bot/__init__.py | head -20"
        );

        // MySQL full table list
        results.mysql_tables = await execCommand(
          "docker exec psvibe-mysql mysql -uroot -p'PsVibe@MySQL2024!' psvibe_api -e 'SHOW FULL TABLES;' 2>&1"
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
