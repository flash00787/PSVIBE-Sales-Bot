const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
let result = '';
conn.on('ready', () => {
  conn.exec(`cat > /tmp/audit_final.py << 'SCRIPTEOF'
import re, os

# Read __init__.py
with open('/root/psvibe-sale-bot/bot/__init__.py') as f:
    content = f.read()

# Find ALL function definitions that have both an api_ call and a gspread fallback
print("=" * 70)
print("FALLBACK ANALYSIS")
print("=" * 70)

# Find functions that use API calls
api_patterns = [
    ('api_fetch_members', 'fetch_members'),
    ('api_fetch_member_data', 'fetch_member_data'),
    ('api_fetch_staff', 'fetch_staff'),
    ('api_fetch_staff_names', 'fetch_staff_names'),
    ('api_fetch_food_prices', 'fetch_food_prices'),
    ('api_fetch_food_costs', 'fetch_food_costs'),
    ('api_fetch_games', 'fetch_games'),
    ('api_fetch_game_library', 'fetch_game_library'),
    ('api_fetch_console_games', 'fetch_console_games'),
    ('api_get_games_on_console', 'get_games_on_console'),
    ('api_get_consoles_with_game', 'get_consoles_with_game'),
    ('api_fetch_base_rate', 'fetch_base_rate'),
    ('api_fetch_console_multiplier', 'fetch_console_multiplier'),
    ('api_fetch_new_member_defaults', 'fetch_new_member_defaults'),
    ('api_fetch_rank_thresholds', 'fetch_rank_thresholds'),
    ('api_fetch_bonus_table', 'fetch_bonus_table'),
    ('api_fetch_rank_table_display', 'fetch_rank_table_display'),
    ('api_fetch_alltime_effective_rate', 'fetch_alltime_effective_rate'),
    ('api_fetch_member_effective_rate', 'fetch_member_effective_rate'),
    ('api_build_member_rate_dict', 'build_member_rate_dict'),
    ('api_fetch_base_salaries', 'fetch_base_salaries'),
    ('api_fetch_attendance', 'fetch_attendance'),
    ('api_fetch_salary_advances', 'fetch_salary_advances'),
    ('api_fetch_promotions_cached', 'fetch_promotions_cached'),
    ('api_fetch_allowed_staff_ids', 'fetch_allowed_staff_ids'),
    ('api_next_voucher', 'next_voucher'),
    ('api_next_member_id', 'next_member_id'),
    ('api_next_member_row_no', 'next_member_row_no'),
    ('api_fetch_referral_code', 'fetch_referral_code'),
    ('api_fetch_console_status', 'fetch_console_status'),
    ('api_fetch_wallet_mins', 'fetch_wallet_mins'),
    ('api_fetch_balance_mins', 'fetch_balance_mins'),
    ('api_fetch_member_tier', 'fetch_member_tier'),
    ('api_create_booking', 'create_booking'),
    ('api_end_booking', 'end_booking'),
    ('api_cancel_booking', 'cancel_booking'),
    ('api_save_attendance', 'save_attendance'),
    ('api_save_receipt_json', 'save_receipt_json'),
    ('api_add_console_game', 'add_console_game'),
    ('api_remove_console_game', 'remove_console_game'),
    ('api_set_game_disc_count', 'set_game_disc_count'),
    ('api_update_game_library_install', 'update_game_library_install'),
    ('api_update_member_effective_rate', 'update_member_effective_rate'),
    ('api_save_referral_code', 'save_referral_code'),
    ('api_add_console_to_setting', 'add_console_to_setting'),
    ('api_remove_console_from_setting', 'remove_console_from_setting'),
    ('api_fetch_sheets_config', 'sheets/config'),
]

# Count how many api_ calls exist in __init__.py
api_call_lines = []
for line_no, line in enumerate(content.split('\\n'), 1):
    for api_func, endpoint in api_patterns:
        if api_func in line and not line.strip().startswith('def ') and not line.strip().startswith('#') and not line.strip().startswith('"') and not line.strip().startswith("'"):
            if api_func not in [l[0] for l in api_call_lines]:
                api_call_lines.append((api_func, line_no))

print("\\nAPI functions CALLED from __init__.py:")
for api_func, line_no in sorted(api_call_lines, key=lambda x: x[1]):
    print(f"  Line {line_no}: {api_func}")

# Check for fallback patterns
print("\\n--- Checking each function for API vs Direct Sheet access ---")

# Look for functions that reference gspread directly
direct_sheet_funcs = []
for line_no, line in enumerate(content.split('\\n'), 1):
    # Find function definitions
    m = re.match(r'^def (\\w+)\\(', line)
    if m:
        fname = m.group(1)
        # Check if this function is called from elsewhere
        if any(name in fname for name in ['fetch_', 'get_', 'next_', 'save_', 'create_', 'end_', 'cancel_', 'update_', 'add_', 'remove_', 'build_', 'set_']):
            if 'api_' not in fname:
                direct_sheet_funcs.append((fname, line_no))

print(f"\\nFunctions using DIRECT sheet access (not API wrappers):")
for fname, line_no in direct_sheet_funcs:
    print(f"  Line {line_no}: {fname}")

# Show key function implementations  
print("\\n" + "=" * 70)
print("FUNCTION CALL FLOW ANALYSIS")
print("=" * 70)

# Find functions and their API vs sheet usage
key_functions = ['fetch_members', 'fetch_staff', 'fetch_attendance', 'save_attendance',
                 'fetch_base_salaries', 'fetch_console_status', 'create_booking', 'end_booking',
                 'next_voucher', 'fetch_wallet_mins', 'fetch_base_rate', 'fetch_food_prices',
                 'fetch_games', 'fetch_console_games', 'get_games_on_console', 'get_consoles_with_game',
                 'fetch_member_data', 'fetch_referral_code', 'save_referral_code', 
                 'fetch_balance_mins', 'fetch_member_effective_rate', 'update_member_effective_rate',
                 'build_member_rate_dict', 'fetch_member_tier', 'fetch_rank_thresholds',
                 'fetch_bonus_table', 'fetch_rank_table_display', 'fetch_new_member_defaults',
                 'fetch_console_multiplier', 'next_member_id', 'next_member_row_no',
                 'fetch_promotions_cached', 'fetch_allowed_staff_ids', 'save_receipt_json',
                 'add_console_game', 'remove_console_game', 'set_game_disc_count',
                 'update_game_library_install', 'add_console_to_setting', 'remove_console_from_setting',
                 'fetch_salary_advances', 'cancel_booking', 'fetch_food_costs',
                 'fetch_staff_names', 'fetch_alltime_effective_rate', 'fetch_sheets_config',
                 'get_att_sh', 'get_booking_sh', 'get_salary_adv_sh', 'get_game_lib_sh', 'get_console_games_sh',
                 'get_consoles_from_setting', 'check_disc_session_conflict']

for fname in key_functions:
    # Find the function definition
    pattern = rf'^def {fname}\\('
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        start = match.start()
        # Get function body (next 20 lines)
        snippet = content[start:start+1500].split('\\n')[:30]
        body = '\\n'.join(snippet)
        
        uses_api = 'api_' in body
        uses_gspread = any(x in body for x in ['setting_sh', 'member_sh', 'wb.worksheet', 'get_booking_sh', 'get_console_games_sh', 'get_game_lib_sh', 'get_att_sh', 'get_salary_adv_sh'])
        
        # Check for try/except
        has_error_handling = 'try:' in body[:500] or 'except' in body[:500]
        
        print(f"\\n--- {fname} ---")
        print(f"  Uses API: {uses_api}")
        print(f"  Uses GSpread Direct: {uses_gspread}")
        print(f"  Has try/except: {has_error_handling}")
        # Show first few meaningful lines
        for line in snippet[1:12]:
            stripped = line.strip()
            if stripped and not stripped.startswith('"') and not stripped.startswith("'"):
                print(f"  {stripped[:100]}")

SCRIPTEOF
python3 /tmp/audit_final.py`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    stream.on('data', (d) => { result += d.toString(); });
    stream.stderr.on('data', (d) => { result += d.toString(); });
    stream.on('close', () => { 
      fs.writeFileSync('/home/node/.openclaw/workspace/audit/fallback_analysis.txt', result);
      console.log(result);
      conn.end(); 
    });
  });
});
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
