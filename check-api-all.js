const { Client } = require('ssh2');
const fs = require('fs');

function execCmd(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) { reject(err); return; }
      let out = '';
      stream.on('data', d => { out += d.toString(); });
      stream.on('close', () => resolve(out));
    });
  });
}

async function main() {
  const conn = new Client();
  await new Promise(r => { conn.on('ready', r); conn.connect({host:'5.223.81.16',port:22,username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')}); });
  console.log('Connected');

  const KEY = 'JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ';
  const BASE = 'http://localhost:8000';

  const endpoints = [
    '/api/fetch_attendance/5%2F28%2F2026',
    '/api/fetch_base_salaries',
    '/api/fetch_food_prices',
    '/api/fetch_food_costs',
    '/api/fetch_console_multiplier/C%20-%2001',
    '/api/fetch_rank_thresholds',
    '/api/fetch_bonus_table',
    '/api/fetch_rank_table_display',
    '/api/next_member_row_no',
    '/api/next_member_id',
    '/api/fetch_wallet_mins/PSV_A_000',
    '/api/fetch_balance_mins/PSV_A_000',
    '/api/fetch_member_tier/PSV_A_000',
    '/api/fetch_member_effective_rate/PSV_A_000',
    '/api/build_member_rate_dict',
    '/api/fetch_console_games',
    '/api/get_games_on_console/C%20-%2001',
    '/api/fetch_console_multiplier/C%20-%2001',
    '/api/fetch_promotions_cached',
    '/api/fetch_game_library',
    '/api/fetch_salary_advances/5%2F28%2F2026',
    '/api/fetch_referral_code/PSV_A_000',
    '/api/fetch_alltime_effective_rate',
  ];

  for (const ep of endpoints) {
    console.log(`\n=== ${ep} ===`);
    const resp = await execCmd(conn, `curl -s "${BASE}${ep}?api_key=${KEY}" | head -c 800`);
    console.log(resp || '(empty)');
  }

  conn.end();
}
main().catch(e => { console.error(e); process.exit(1); });
