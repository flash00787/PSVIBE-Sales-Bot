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

  // Read full V2 files (wc to check sizes)
  for (const f of ['sales.py', 'members.py', 'referral.py', 'discount.py']) {
    const fpath = `${V2_BASE}/${f}`;
    let rr = await sshExec(conn, `wc -l ${fpath} 2>/dev/null || echo "NOT FOUND"`);
    console.log(`${f}: ${rr.stdout.trim()}`);
  }

  // Read full referral.py and discount.py (they're small)
  console.log('\n=== FULL referral.py ===');
  let r = await sshExec(conn, `cat ${V2_BASE}/referral.py`);
  console.log(r.stdout);

  console.log('\n=== FULL discount.py ===');
  r = await sshExec(conn, `cat ${V2_BASE}/discount.py`);
  console.log(r.stdout);

  // Read full sales.py
  console.log('\n=== FULL sales.py ===');
  r = await sshExec(conn, `cat ${V2_BASE}/sales.py`);
  console.log(r.stdout);

  // Read full members.py
  console.log('\n=== FULL members.py ===');
  r = await sshExec(conn, `cat ${V2_BASE}/members.py`);
  console.log(r.stdout);

  // Search V1 for specific function signatures we need
  console.log('\n=== V1: fetch_base_rate ===');
  r = await sshExec(conn, `grep -n -A 30 "^async def fetch_base_rate\\|^def fetch_base_rate" ${V1_MAIN}`);
  console.log(r.stdout);

  console.log('\n=== V1: fetch_console_multiplier ===');
  r = await sshExec(conn, `grep -n -A 20 "^async def fetch_console_multiplier\\|^def fetch_console_multiplier" ${V1_MAIN}`);
  console.log(r.stdout);

  console.log('\n=== V1: fetch_console_status ===');
  r = await sshExec(conn, `grep -n -A 25 "^async def fetch_console_status\\|^def fetch_console_status" ${V1_MAIN}`);
  console.log(r.stdout);

  console.log('\n=== V1: fetch_member_data ===');
  r = await sshExec(conn, `grep -n -A 35 "^async def fetch_member_data\\|^def fetch_member_data" ${V1_MAIN}`);
  console.log(r.stdout);

  console.log('\n=== V1: fetch_promotions_cached ===');
  r = await sshExec(conn, `grep -n -A 30 "^async def fetch_promotions_cached\\|^def fetch_promotions_cached" ${V1_MAIN}`);
  console.log(r.stdout);

  console.log('\n=== V1: fetch_referral_code ===');
  r = await sshExec(conn, `grep -n -A 15 "^async def fetch_referral_code\\|^def fetch_referral_code" ${V1_MAIN}`);
  console.log(r.stdout);

  console.log('\n=== V1: save_referral_code ===');
  r = await sshExec(conn, `grep -n -A 15 "^async def save_referral_code\\|^def save_referral_code" ${V1_MAIN}`);
  console.log(r.stdout);

  console.log('\n=== V1: display_rank ===');
  r = await sshExec(conn, `grep -n -A 10 "^async def display_rank\\|^def display_rank" ${V1_MAIN}`);
  console.log(r.stdout);

  console.log('\n=== V1: rank_emoji ===');
  r = await sshExec(conn, `grep -n -A 10 "^async def rank_emoji\\|^def rank_emoji" ${V1_MAIN}`);
  console.log(r.stdout);

  console.log('\n=== V1: step_hdr ===');
  r = await sshExec(conn, `grep -n -A 15 "^def step_hdr" ${V1_MAIN}`);
  console.log(r.stdout);

  conn.end();
}

main().catch(err => {
  console.error('FATAL:', err);
  process.exit(1);
});
