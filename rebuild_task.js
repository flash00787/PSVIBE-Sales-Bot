const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '167.71.196.120';
const PORT = 22;
const USERNAME = 'root';
const PRIVATE_KEY_PATH = path.join(__dirname, '.ssh', 'id_rsa');
const V1_MAIN = '/root/staging/monolithic_ref/main.py';
const V2_BASE = '/root/staging/bot_src/bot/handlers';
const DEPLOY_BASE = '/root/Sales-Tele-Bot_refactored/bot/handlers';

const FILES = ['sales.py', 'members.py', 'referral.py', 'discount.py'];

function sshExec(conn, cmd, timeout = 30000) {
  return new Promise((resolve, reject) => {
    let stdout = '', stderr = '';
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      stream.on('data', (data) => { stdout += data.toString(); });
      stream.stderr.on('data', (data) => { stderr += data.toString(); });
      stream.on('close', (code) => {
        resolve({ code, stdout, stderr });
      });
    });
  });
}

function connect() {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => resolve(conn));
    conn.on('error', reject);
    conn.connect({
      host: HOST,
      port: PORT,
      username: USERNAME,
      privateKey: fs.readFileSync(PRIVATE_KEY_PATH),
    });
  });
}

async function main() {
  const conn = await connect();
  console.log('=== Connected to VPS ===\n');

  // Step 1: Search V1 for relevant functions
  console.log('--- STEP 1: V1 Function Search ---');
  let r = await sshExec(conn, `grep -n "^async def \\|^def " ${V1_MAIN} | grep -i "step_\\|prompt_\\|cmd_\\|_check_\\|_end_session\\|_show_\\|cb_\\|prompt_tu\\|step_tu\\|prompt_nm\\|step_nm\\|prompt_discount\\|step_discount\\|prompt_promo\\|step_promo\\|prompt_referral\\|step_referral\\|prompt_staff\\|step_staff\\|step_bundle"`, 45000);
  console.log('V1 Functions Found:', r.code);
  if (r.stdout) console.log(r.stdout.substring(0, 6000));
  if (r.stderr) console.error('STDERR:', r.stderr.substring(0, 1000));

  // Step 2: Read current V2 files
  console.log('\n--- STEP 2: Current V2 Files ---');
  for (const f of FILES) {
    const fpath = `${V2_BASE}/${f}`;
    let rr = await sshExec(conn, `cat ${fpath} 2>/dev/null || echo "FILE NOT FOUND"`);
    console.log(`\n=== ${f} (${(rr.stdout || '').length} chars) ===`);
    if (rr.stdout && rr.stdout !== 'FILE NOT FOUND\n') {
      console.log(rr.stdout.substring(0, 8000));
    } else {
      console.log('FILE NOT FOUND');
    }
  }

  conn.end();
  console.log('\n=== DONE reading files ===');
}

main().catch(err => {
  console.error('FATAL:', err);
  process.exit(1);
});
