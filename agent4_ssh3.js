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

        // MySQL password from env/docker inspect
        results.mysql_env = await execCommand(
          "docker inspect psvibe-mysql --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null"
        );

        // Try common pswd patterns
        results.mysql_try = await execCommand(
          "docker exec psvibe-mysql mysql -uroot -e 'SHOW DATABASES;' 2>&1" // no pswd
        );
        
        // Check docker-compose or env files for pswd
        results.env_file = await execCommand(
          "cat /root/psvibe-sale-bot/.env 2>/dev/null | grep -i 'MYSQL\\|DB_' | head -20; cat /root/Sales-Tele-Bot_refactored/.env 2>/dev/null | grep -i 'MYSQL\\|DB_' | head -10"
        );

        // V1 api_client.py
        results.v1_apiclient = await execCommand(
          "cat /root/psvibe-sale-bot/bot/api_client.py 2>/dev/null"
        );

        // V1 __init__.py (the bot module init - where gspread connections are)
        results.v1_init = await execCommand(
          "head -100 /root/psvibe-sale-bot/bot/__init__.py 2>/dev/null"
        );

        // V1 app.py (where sheet writes likely happen)
        results.v1_app_head = await execCommand(
          "head -80 /root/psvibe-sale-bot/bot/app.py 2>/dev/null"
        );

        // Search V1 handlers for direct gspread usage (not in sqlite/)
        results.v1_handlers_gspread = await execCommand(
          "grep -rn 'worksheet\\|gspread\\|gc\\.' /root/psvibe-sale-bot/bot/handlers/ 2>/dev/null | grep -v __pycache__ | head -30"
        );

        // V2 init
        results.v2_init = await execCommand(
          "head -100 /tmp/v2_check2/Sales-Tele-Bot_refactored/bot/__init__.py 2>/dev/null"
        );

        // Check MySQL databases (try with docker exec)
        results.mysql_root = await execCommand(
          "docker exec psvibe-mysql mysql -uroot -p'psvibe_root_2024' -e 'SHOW DATABASES;' 2>&1"
        );

        // Check for any docker-compose files
        results.compose = await execCommand(
          "find /root -name 'docker-compose*' -o -name 'compose*' 2>/dev/null | head -20"
        );

        // Check current V1 running process sheet config
        results.v1_main_head = await execCommand(
          "head -30 /root/psvibe-sale-bot/main.py"
        );

        // Check sqlite db path
        results.sqlite_db = await execCommand(
          "find /root/psvibe-sale-bot -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' 2>/dev/null"
        );

        // Check V2 sqlite db
        results.v2_sqlite_db = await execCommand(
          "find /tmp/v2_check2 -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' 2>/dev/null"
        );

        // Check V2 customer_bot api.py (the one found)
        results.v2_customer_api = await execCommand(
          "cat /tmp/v2_check2/Sales-Tele-Bot_refactored/customer_bot/api.py 2>/dev/null | head -50"
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
