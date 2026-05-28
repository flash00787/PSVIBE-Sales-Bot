const fs = require('fs');

const files = {
  main: fs.readFileSync('/home/node/.openclaw/workspace/audit_files/_root_Aung_Chan_Myint_Sales-Tele-Bot_main.py', 'utf8'),
  init: fs.readFileSync('/home/node/.openclaw/workspace/audit_files/_root_Aung_Chan_Myint_Sales-Tele-Bot_bot___init__.py', 'utf8'),
  app: fs.readFileSync('/home/node/.openclaw/workspace/audit_files/_root_Aung_Chan_Myint_Sales-Tele-Bot_bot_app.py', 'utf8'),
  handlers: fs.readFileSync('/home/node/.openclaw/workspace/audit_files/_root_Aung_Chan_Myint_Sales-Tele-Bot_bot_handlers.py', 'utf8'),
};

// Extract function boundaries
function getFunctionBoundaries(code, funcName) {
  const regex = new RegExp(`^(async\\s+)?def\\s+${funcName}\\s*\\(`, 'm');
  const match = regex.exec(code);
  if (!match) return null;
  const startIdx = code.lastIndexOf('\n', match.index) + 1; // start of line with def
  // find end - next top-level def or end of file
  const restStart = match.index + match[0].length;
  const nextDefMatch = /^(async\s+)?def\s+\w+\s*\(/.exec(code.slice(restStart));
  const endIdx = nextDefMatch ? restStart + code.slice(restStart).lastIndexOf('\n', nextDefMatch.index) + 1 : code.length;
  return code.substring(startIdx, endIdx);
}

// Get function bodies for comparison
function compareFunctions(name) {
  let v1Match = getFunctionBoundaries(files.main, name);
  let v2Match = getFunctionBoundaries(files.handlers, name);
  if (!v2Match) v2Match = getFunctionBoundaries(files.init, name);
  if (!v2Match) v2Match = getFunctionBoundaries(files.app, name);
  
  if (!v1Match && !v2Match) return null;
  
  if (v1Match && v2Match) {
    // Quick comparison
    const v1Len = v1Match.length;
    const v2Len = v2Match.length;
    const sizeDiff = v2Len - v1Len;
    const pctDiff = ((sizeDiff / v1Len) * 100).toFixed(1);
    return {
      name,
      v1Len,
      v2Len,
      sizeDiff,
      pctDiff: pctDiff + '%',
    };
  }
  return { name, v1Len: v1Match ? v1Match.length : null, v2Len: v2Match ? v2Match.length : null };
}

// Compare key functions with significant size differences
console.log('=== SIZE DIFFERENCES FOR SHARED FUNCTIONS ===');
const shared = [
  'show_main_menu', 'step_mm_menu', 'cmd_payroll', 'cmd_today_report',
  'cmd_financial_report', 'calc_monthly_pnl', 'calc_monthly_payroll',
  '_sale_bg', '_tu_bg', 'cmd_broadcast', 'step_sale_confirm',
  'cmd_admin_bookings', '_do_booking_action', 'show_finance_menu',
  'step_nm_confirm', 'step_tu_confirm', 'show_stock_menu',
  'prompt_book_console', 'step_book_console', 'show_console_menu',
  'launch_session_sale', '_remind_loop', '_sale_bg', '_nm_bg',
  'main', '_set_commands'
];

const diffs = [];
shared.forEach(name => {
  const r = compareFunctions(name);
  if (r && r.v1Len && r.v2Len) {
    diffs.push(r);
  }
});
diffs.sort((a, b) => Math.abs(b.sizeDiff) - Math.abs(a.sizeDiff));
diffs.forEach(d => console.log(`  ${d.name}: V1=${d.v1Len} V2=${d.v2Len} diff=${d.sizeDiff} (${d.pctDiff})`));

// Check _sigterm_handler
console.log('\n=== _sigterm_handler (only in V1) ===');
const sigtermV1 = getFunctionBoundaries(files.main, '_sigterm_handler');
if (sigtermV1) console.log(sigtermV1.trim().substring(0, 500));

// Check where main() is
console.log('\n=== main() function comparison ===');
console.log('V1 main size:', getFunctionBoundaries(files.main, 'main')?.length);
console.log('V2 main size:', getFunctionBoundaries(files.app, 'main')?.length);

// Check V2-specific new functions
console.log('\n=== V2 NEW FUNCTIONS (check implementations) ===');
const newFuncs = ['check_disc_session_conflict', 'fetch_promotions_cached', '_replit_delete', 
  'fetch_referral_code', 'save_referral_code', '_auth_middleware', 'cb_home',
  'prompt_nm_referral', 'step_nm_referral', '_show_nm_confirm', 'prompt_adjust_time',
  'step_adjust_time', '_mds', '_mark_bk_completed', '_session_end_notify',
  'prompt_promo_select', 'step_promo_select', 'step_bundle_foc', '_PLACEHOLDER_prompt_discount',
  '_wl_console_availability', '_fmt_mmt_dt', '_wl_status_label', '_wl_pref_label',
  'cmd_waitlist_mgmt', '_show_wl_menu', 'step_wl_menu', 'cb_wl_action',
  'cmd_promo_reports', 'prompt_book_link', '_in_window', '_show_console_select',
  'step_book_link', 'cb_booking_arrive', 'step_game_edit_select', 'step_game_edit_field',
  'step_game_edit_value', 'prompt_referral_code', 'step_referral_code', 'main'];

newFuncs.forEach(name => {
  const v2Body = getFunctionBoundaries(files.handlers, name) || getFunctionBoundaries(files.init, name) || getFunctionBoundaries(files.app, name);
  if (v2Body) {
    const lines = v2Body.split('\n').filter(l => l.trim()).length;
    console.log(`  ${name}: ${v2Body.length} chars, ~${lines} lines`);
  } else {
    console.log(`  ${name}: NOT FOUND`);
  }
});

// Check if V1 has referral code functionality
console.log('\n=== Referral Code in V1? ===');
const refInV1 = files.main.match(/referral/i);
console.log('V1 referral mentions:', refInV1 ? refInV1.length : 0);

// Check if V1 has waitlist functionality
console.log('\n=== Waitlist in V1? ===');
const wlInV1 = files.main.match(/waitlist|wait_list|wl_/gi);
console.log('V1 waitlist mentions:', wlInV1 ? wlInV1.length : 0);

// Check if V1 has promotions functionality  
console.log('\n=== Promotions/Promo in V1? ===');
const promoInV1 = files.main.match(/promo/gi);
console.log('V1 promo mentions:', promoInV1 ? promoInV1.length : 0);

// Check booking_arrive in V1
console.log('\n=== booking_arrive in V1? ===');
const arriveInV1 = files.main.match(/arrive/gi);
console.log('V1 arrive mentions:', arriveInV1 ? arriveInV1.length : 0);

// Import differences
console.log('\n=== IMPORT COMPARISON ===');
const v1Imports = [];
const v2Imports = [];

files.main.split('\n').forEach(line => {
  const trimmed = line.trim();
  if (trimmed.match(/^(from\s+\S+\s+import|import\s+)/)) v1Imports.push(trimmed);
});

(files.init + '\n' + files.app + '\n' + files.handlers).split('\n').forEach(line => {
  const trimmed = line.trim();
  if (trimmed.match(/^(from\s+\S+\s+import|import\s+)/)) v2Imports.push(trimmed);
});

console.log('V1 imports:');
v1Imports.forEach(i => console.log('  ' + i));
console.log('\nV2 imports not in V1:');
const v1ImportSet = new Set(v1Imports.map(i => i.replace(/\s+/g, ' ')));
const v2OnlyImports = v2Imports.filter(i => !v1ImportSet.has(i.replace(/\s+/g, ' ')));
v2OnlyImports.forEach(i => console.log('  ' + i));
