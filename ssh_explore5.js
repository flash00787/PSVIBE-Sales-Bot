const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

conn.on('ready', () => {
  conn.exec("grep -n 'def fetch_members\\|def fetch_member_data\\|def fetch_wallet_mins\\|def fetch_member_tier\\|def fetch_staff\\|def fetch_food_prices\\|def fetch_food_costs\\|def fetch_base_rate\\|def fetch_console_multiplier\\|def fetch_new_member_defaults\\|def fetch_rank_thresholds\\|def fetch_bonus_table\\|def fetch_alltime_effective_rate\\|def fetch_member_effective_rate\\|def build_member_rate_dict\\|def fetch_base_salaries\\|def fetch_attendance\\|def fetch_salary_advances\\|def fetch_promotions_cached\\|def fetch_allowed_staff_ids\\|def next_voucher\\|def next_member_id\\|def next_member_row_no\\|def next_write_row\\|def fetch_referral_code\\|def save_attendance\\|def save_receipt_json\\|def update_member_effective_rate\\|def save_referral_code\\|def fetch_rank_table_display' /root/backups/v1_standalone/main.py", (err, stream) => {
    if (err) { console.error('ERROR:', err); conn.end(); return; }
    let data = '';
    stream.on('data', (chunk) => { data += chunk.toString(); });
    stream.stderr.on('data', (chunk) => { console.error('STDERR:', chunk.toString()); });
    stream.on('close', (code) => {
      console.log('EXIT:', code);
      console.log(data);
      conn.end();
    });
  });
});
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: key });
