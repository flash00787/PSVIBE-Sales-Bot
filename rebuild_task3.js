const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '167.71.196.120';
const PORT = 22;
const USERNAME = 'root';
const PRIVATE_KEY_PATH = path.join(__dirname, '.ssh', 'id_rsa');
const V1_MAIN = '/root/staging/monolithic_ref/main.py';

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

  // Search for missing functions in V1
  for (const fn of ['fetch_referral_code', 'save_referral_code', 'fetch_promotions_cached',
                     'fetch_promotions', 'fetch_rank_table_display', 'fetch_bonus_table',
                     'get_bonus_mins', 'next_member_id', 'get_receipt_kb', 'next_member_row_no',
                     'fetch_member_tier', 'fetch_balance_mins', 'fetch_member_effective_rate',
                     'fetch_alltime_effective_rate', 'fetch_wallet_mins',
                     'update_member_effective_rate', 'get_customer_chat_id', 'get_member_rank',
                     'end_booking', 'calc_duration', 'now_mmt', 'save_receipt_json',
                     'next_write_row', 'next_voucher', 'today_str',
                     '_replit_get', '_replit_post', '_replit_patch', '_cancel_remind',
                     '_check_low_balance_alert', '_get_member_rows', '_get_cfg',
                     'show_main_menu', 'show_console_menu', 'cmd_cancel']) {
    let r = await sshExec(conn, `grep -n -c "^async def ${fn}\\|^def ${fn}" ${V1_MAIN}`);
    const count = parseInt(r.stdout.trim()) || 0;
    console.log(`${fn}: found in V1 = ${count > 0 ? 'YES' + (count > 1 ? ' ('+count+' defs)' : '') : 'NO'}`);
  }

  // Also check the V2 bot's __init__.py to see what's actually exported
  console.log('\n=== V2 bot/__init__.py (first 50 lines) ===');
  let r = await sshExec(conn, `head -50 /root/Sales-Tele-Bot_refactored/bot/__init__.py`);
  console.log(r.stdout);

  // Check handlers/__init__.py
  console.log('\n=== V2 handlers/__init__.py ===');
  r = await sshExec(conn, `cat /root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py`);
  console.log(r.stdout);

  // Verify deploy target exists
  console.log('\n=== Deploy target ===');
  r = await sshExec(conn, `ls -la /root/Sales-Tele-Bot_refactored/bot/handlers/sales.py /root/Sales-Tele-Bot_refactored/bot/handlers/members.py /root/Sales-Tele-Bot_refactored/bot/handlers/referral.py /root/Sales-Tele-Bot_refactored/bot/handlers/discount.py 2>&1`);
  console.log(r.stdout);

  conn.end();
}

main().catch(err => {
  console.error('FATAL:', err);
  process.exit(1);
});
