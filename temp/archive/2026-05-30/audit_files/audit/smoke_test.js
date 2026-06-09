const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();
const AK = 'JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ';

function sh(strings, ...vals) {
  // Escape $ in template strings for shell
  let result = '';
  for (let i = 0; i < strings.length; i++) {
    result += strings[i].replace(/\$/g, '\\$');
    if (i < vals.length) result += vals[i];
  }
  return result;
}

// Build the full shell script
const fullScript = [
  '#!/bin/bash',
  'AK="' + AK + '"',
  '',
  'echo "=== PART 1: GET endpoints ==="',
  'for ep in health fetch_console_status fetch_members fetch_staff fetch_staff_names fetch_food_prices fetch_food_costs fetch_games fetch_game_library fetch_console_games fetch_consoles_with_game fetch_base_rate fetch_new_member_defaults fetch_rank_thresholds fetch_bonus_table fetch_rank_table_display fetch_alltime_effective_rate fetch_base_salaries fetch_promotions_cached fetch_allowed_staff_ids next_voucher next_member_id next_member_row_no sheets/config analytics/dashboard analytics/daily_sales analytics/topups analytics/member_activity analytics/console_usage analytics/weekly_trends mysql/health mysql/sync_status; do',
  '  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "localhost:8000/api/$ep?api_key=$AK")',
  '  echo "GET $ep -> $code"',
  'done',
  '',
  'echo ""',
  'echo "=== PART 2: Param endpoints ==="',
  'for param in "fetch_member_data/1" "fetch_wallet_mins/1" "fetch_balance_mins/1" "fetch_member_tier/1" "fetch_console_multiplier/PS5" "fetch_member_effective_rate/1" "fetch_referral_code/1" "get_games_on_console/PS5" "end_booking/1" "cancel_booking/1" "remove_console_from_setting/1"; do',
  '  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "localhost:8000/api/$param?api_key=$AK")',
  '  echo "GET $param -> $code"',
  'done',
  '',
  'echo ""',
  'echo "=== PART 3: POST endpoints ==="',
  'code=$(curl -s -X POST -o /dev/null -w "%{http_code}" --max-time 15 "localhost:8000/api/create_booking?api_key=$AK" -H "Content-Type: application/json" -d \'{}\')',
  'echo "POST create_booking -> $code"',
  'code=$(curl -s -X POST -o /dev/null -w "%{http_code}" --max-time 15 "localhost:8000/api/save_attendance?api_key=$AK" -H "Content-Type: application/json" -d \'{}\')',
  'echo "POST save_attendance -> $code"',
  '',
  'echo ""',
  'echo "=== PART 4: Non-200 body capture ==="',
  'for ep in health fetch_console_status fetch_members fetch_staff fetch_staff_names fetch_food_prices fetch_food_costs fetch_games fetch_game_library fetch_console_games fetch_consoles_with_game fetch_base_rate fetch_new_member_defaults fetch_rank_thresholds fetch_bonus_table fetch_rank_table_display fetch_alltime_effective_rate fetch_base_salaries fetch_promotions_cached fetch_allowed_staff_ids next_voucher next_member_id next_member_row_no sheets/config analytics/dashboard analytics/daily_sales analytics/topups analytics/member_activity analytics/console_usage analytics/weekly_trends mysql/health mysql/sync_status fetch_member_data/1 fetch_wallet_mins/1 fetch_balance_mins/1 fetch_member_tier/1 fetch_console_multiplier/PS5 fetch_member_effective_rate/1 fetch_referral_code/1 get_games_on_console/PS5 end_booking/1 cancel_booking/1 remove_console_from_setting/1; do',
  '  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "localhost:8000/api/$ep?api_key=$AK")',
  '  if [ "$code" != "200" ]; then',
  '    body=$(curl -s --max-time 15 "localhost:8000/api/$ep?api_key=$AK" | head -c 500)',
  '    echo "NON200 GET $ep -> $code ||| $body"',
  '  fi',
  'done',
  '',
  'echo ""',
  'echo "=== POST NON-200 ==="',
  'for ep in create_booking save_attendance; do',
  '  code=$(curl -s -X POST -o /dev/null -w "%{http_code}" --max-time 15 "localhost:8000/api/$ep?api_key=$AK" -H "Content-Type: application/json" -d \'{}\')',
  '  if [ "$code" != "200" ]; then',
  '    body=$(curl -s -X POST --max-time 15 "localhost:8000/api/$ep?api_key=$AK" -H "Content-Type: application/json" -d \'{}\' | head -c 500)',
  '    echo "NON200 POST $ep -> $code ||| $body"',
  '  fi',
  'done',
  '',
  'echo ""',
  'echo "=== ALL DONE ==="',
].join('\n');

let allOutput = '';

conn.on('ready', () => {
  console.log('SSH connected, running tests...\n');
  conn.exec(fullScript, (err, stream) => {
    if (err) throw err;
    stream.on('data', (data) => {
      process.stdout.write(data.toString());
      allOutput += data.toString();
    });
    stream.stderr.on('data', (data) => {
      process.stderr.write('STDERR: ' + data.toString());
    });
    stream.on('close', (code) => {
      console.log(`\n--- Stream closed, code ${code} ---`);
      
      const report = parseResults(allOutput);
      const outDir = '/home/node/.openclaw/workspace/audit';
      if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
      fs.writeFileSync(path.join(outDir, 'sales_bot_api_smoke.md'), report);
      console.log('Report written.');
      conn.end();
    });
  });
});

conn.on('error', (err) => {
  console.error('SSH error:', err);
  process.exit(1);
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
});

function parseResults(output) {
  const lines = output.split('\n');
  const working = [];
  const broken = [];
  const non200Bodies = {};
  
  // First collect non-200 bodies
  for (const line of lines) {
    const nm = line.match(/^NON200 (GET|POST) (.+?) -> (\d+) \|\|\| (.+)/);
    if (nm) {
      const key = nm[1] + ' ' + nm[2];
      non200Bodies[key] = { code: nm[3], body: nm[4] };
    }
  }
  
  // Then collect all results
  for (const line of lines) {
    const m = line.match(/^(GET|POST)\s+(.+?)\s+->\s+(\d+)/);
    if (m) {
      const key = m[1] + ' ' + m[2];
      const code = parseInt(m[3]);
      if (code === 200) {
        working.push(key);
      } else {
        const extra = non200Bodies[key];
        let bodyStr = '';
        if (extra) bodyStr = extra.body.substring(0, 200);
        broken.push(`${key} → ${code}${bodyStr ? '\n  Body: ' + bodyStr : ''}`);
      }
    }
  }
  
  const total = working.length + broken.length;
  
  return `# API Smoke Test Results
**Date:** ${new Date().toISOString().replace('T', ' ').substring(0, 19)} UTC
**Server:** 5.223.81.16:8000
**Total endpoints tested:** ${total}

## ✅ Working (200) — ${working.length} endpoints
${working.map(e => `- ${e}`).join('\n')}

## ❌ Broken (4xx/5xx) — ${broken.length} endpoints
${broken.length > 0 ? broken.map(e => `- ${e}`).join('\n\n') : 'None! All endpoints returned 200.'}

## Notes
- All tests used API key: JWIErd82...
- POST endpoints tested with empty JSON body: create_booking, save_attendance
- Timeout: 15s per endpoint
`;
}
