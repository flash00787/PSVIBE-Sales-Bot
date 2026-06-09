const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

function runCmd(cmd, label) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', (data) => { stdout += data.toString(); });
      stream.stderr.on('data', (data) => { stderr += data.toString(); });
      stream.on('close', (code) => {
        resolve({ label, stdout, stderr, code });
      });
    });
  });
}

conn.on('ready', async () => {
  console.log('=== SSH CONNECTED ===\n');

  // Step 1: Full directory scan
  console.log('=== STEP 1: Full customer_bot directory scan ===');
  let r = await runCmd('find /root/psvibe-sale-bot/customer_bot/ -type f | sort', 'find');
  console.log('FILES:');
  console.log(r.stdout);
  if (r.stderr) console.log('STDERR:', r.stderr);

  r = await runCmd('wc -l /root/psvibe-sale-bot/customer_bot/*.py 2>/dev/null | tail -5', 'wc');
  console.log('LINE COUNTS:');
  console.log(r.stdout);

  r = await runCmd('find /root/psvibe-sale-bot/customer_bot/ -type f -name "*.py" | wc -l', 'pycount');
  console.log('PY FILE COUNT:', r.stdout.trim());

  // Step 2: Check main.py
  console.log('\n=== STEP 2: customer_bot/main.py ===');
  r = await runCmd('cat /root/psvibe-sale-bot/customer_bot/main.py 2>/dev/null', 'main.py');
  console.log(r.stdout || 'FILE NOT FOUND');
  if (r.stderr) console.log('STDERR:', r.stderr);

  // Step 3: Check for V1 dependencies (imports, paths, etc.)
  console.log('\n=== STEP 3: V1 Dependency Analysis ===');
  const patterns = [
    'sys\\\\.path',
    'chdir',
    'from bot',
    'from \\\\.\\\\.',
    '/root/',
    'import bot',
    'import main',
    'from main'
  ];
  for (const pat of patterns) {
    r = await runCmd(`grep -rn '${pat}' /root/psvibe-sale-bot/customer_bot/ 2>/dev/null`, `grep:${pat}`);
    if (r.stdout.trim()) {
      console.log(`\n--- Pattern: ${pat} ---`);
      console.log(r.stdout);
    }
  }

  // Additional broader dependency scan
  console.log('\n--- All import statements ---');
  r = await runCmd("grep -rn '^import \\|^from ' /root/psvibe-sale-bot/customer_bot/ 2>/dev/null", 'imports');
  console.log(r.stdout);

  // Step 4: Service definition
  console.log('\n=== STEP 4: Customer Bot Service ===');
  r = await runCmd('cat /etc/systemd/system/psvibe_customer_bot.service 2>/dev/null', 'service');
  console.log(r.stdout || 'FILE NOT FOUND');

  r = await runCmd('systemctl cat psvibe_customer_bot 2>/dev/null', 'systemctl');
  console.log(r.stdout || 'SYSTEMCTL: not found');

  // Step 5: Shared resources
  console.log('\n=== STEP 5: Shared Resources (sheets, APIs) ===');
  r = await runCmd("grep -rn 'sheet\\|spreadsheet\\|gspread\\|api_client\\|fetch_\\|api\\.py\\|sheets' /root/psvibe-sale-bot/customer_bot/ 2>/dev/null | head -40", 'shared');
  console.log(r.stdout);

  // Step 6: .env config
  console.log('\n=== STEP 6: .env Config ===');
  r = await runCmd('head -30 /root/psvibe-sale-bot/.env 2>/dev/null', 'env');
  console.log(r.stdout || 'FILE NOT FOUND');

  // Extra: check for any shared files/libraries
  console.log('\n=== EXTRA: Shared libs / common imports ===');
  r = await runCmd("grep -rn 'from bot\\|from utils\\|from config\\|from database\\|from handlers' /root/psvibe-sale-bot/customer_bot/ 2>/dev/null", 'shared_modules');
  console.log(r.stdout || 'No shared module imports found');

  // Check the bot's own directory structure for any __init__.py
  console.log('\n=== EXTRA: __init__.py files ===');
  r = await runCmd("find /root/psvibe-sale-bot/customer_bot/ -name '__init__.py' 2>/dev/null", 'inits');
  console.log(r.stdout || 'No __init__.py found');

  // Check if there is a separate requirements.txt for customer_bot
  console.log('\n=== EXTRA: requirements.txt ===');
  r = await runCmd('cat /root/psvibe-sale-bot/customer_bot/requirements.txt 2>/dev/null', 'reqs');
  console.log(r.stdout || 'No customer_bot/requirements.txt');

  r = await runCmd('cat /root/psvibe-sale-bot/requirements.txt 2>/dev/null', 'parent_reqs');
  console.log('\nParent requirements.txt:');
  console.log(r.stdout || 'No parent requirements.txt');

  // Check customer bot's own directory listing in detail
  console.log('\n=== EXTRA: Directory structure ===');
  r = await runCmd('ls -la /root/psvibe-sale-bot/customer_bot/ 2>/dev/null', 'ls');
  console.log(r.stdout);

  // Check all files that might reference V1
  console.log('\n=== EXTRA: References to V1 files/paths ===');
  r = await runCmd("grep -rn 'psvibe\\|/root/psvibe' /root/psvibe-sale-bot/customer_bot/ 2>/dev/null", 'psvibe_refs');
  console.log(r.stdout);

  conn.end();
});

conn.on('error', (err) => {
  console.error('SSH CONNECTION ERROR:', err);
  process.exit(1);
});

conn.connect({
  host: HOST,
  port: 22,
  username: USER,
  privateKey: fs.readFileSync(KEY_PATH),
  readyTimeout: 15000
});
