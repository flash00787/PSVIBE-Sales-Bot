const fs = require('fs');

const files = {
  main: fs.readFileSync('/home/node/.openclaw/workspace/audit_files/_root_Aung_Chan_Myint_Sales-Tele-Bot_main.py', 'utf8'),
  init: fs.readFileSync('/home/node/.openclaw/workspace/audit_files/_root_Aung_Chan_Myint_Sales-Tele-Bot_bot___init__.py', 'utf8'),
  app: fs.readFileSync('/home/node/.openclaw/workspace/audit_files/_root_Aung_Chan_Myint_Sales-Tele-Bot_bot_app.py', 'utf8'),
  handlers: fs.readFileSync('/home/node/.openclaw/workspace/audit_files/_root_Aung_Chan_Myint_Sales-Tele-Bot_bot_handlers.py', 'utf8'),
};

// Check signal handling in V1 vs V2
console.log('=== SIGNAL HANDLING ===');
console.log('V1 signal imports:', files.main.match(/signal/g) ? files.main.match(/signal/g).length : 0);
console.log('V2 signal imports:', (files.init + files.app + files.handlers).match(/signal/g)?.length || 0);

// Check _sigterm_handler in V1
const sigV1 = files.main.indexOf('_sigterm_handler');
console.log('V1 _sigterm_handler at byte:', sigV1);
if (sigV1 >= 0) {
  console.log('V1 sigterm context:\n', files.main.substring(sigV1, sigV1 + 500));
}

// Check how V2 handles shutdown
console.log('\n=== V2 SHUTDOWN HANDLING ===');
const shutdownV2 = (files.app).match(/shutdown|SIGTERM|SIGINT|signal|stop|idle|close/gi);
console.log('V2 shutdown-related mentions:', shutdownV2 ? shutdownV2.length : 0, shutdownV2);

// Check V2 app.py main function
console.log('\n=== V2 app.py main() ===');
const mainStart = files.app.indexOf('def main():');
const mainEnd = files.app.indexOf('\ndef ', mainStart + 10);
const mainBody = files.app.substring(mainStart, mainEnd > 0 ? mainEnd : files.app.length);
console.log(mainBody.substring(0, 3000));

// Check V1 main function for comparison
console.log('\n=== V1 main() first 2000 chars ===');
const mainV1Start = files.main.indexOf('def main():');
const mainV1End = files.main.indexOf('\ndef ', mainV1Start + 10);
console.log(files.main.substring(mainV1Start, Math.min(mainV1Start + 2000, mainV1End)));

// Check error_handler differences
console.log('\n=== ERROR HANDLER COMPARISON ===');
function findFunc(code, name) {
  const idx = code.indexOf(`def ${name}(`);
  if (idx < 0) return null;
  const startLine = code.substring(0, idx).split('\n').length;
  const nextDef = code.indexOf('\ndef ', idx + 10);
  const endIdx = nextDef > 0 ? code.lastIndexOf('\n', nextDef) : code.length;
  return { startLine, body: code.substring(idx, endIdx).substring(0, 800) };
}

const v1Err = findFunc(files.main, 'error_handler');
const v2Err = findFunc(files.handlers, 'error_handler');
if (v1Err) console.log('V1 error_handler (line ' + v1Err.startLine + '):\n' + v1Err.body);
if (v2Err) console.log('\nV2 error_handler:\n' + v2Err.body);

// Check _auth_middleware in V1 vs V2
console.log('\n=== AUTH MIDDLEWARE ===');
const authV1 = files.main.match(/ALLOWED_USER_IDS|allowed_users|authorize/i);
console.log('V1 auth mentions:', authV1 ? authV1.length : 0);
if (authV1) authV1.forEach(m => console.log('  ', m));

// Check command registration
console.log('\n=== COMMAND REGISTRATION ===');
function findFuncFull(code, name) {
  const idx = code.indexOf(`def ${name}(`);
  if (idx < 0) return idx;
  const start = code.lastIndexOf('\n', idx) + 1;
  // find next top-level def
  let next = start;
  let depth = 0;
  const lines = code.substring(idx).split('\n');
  let endRecent = idx + lines[0].length + 1;
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    endRecent += line.length + 1;
    if (line.match(/^(async\s+)?def\s+\w+\s*\(/) && depth === 0) {
      // back up to before this def
      return code.substring(start, idx + code.substring(idx).split('\n').slice(0, i).join('\n').length);
    }
    if (line.trim().startsWith('def ') || line.trim().match(/^async\s+def\s+/)) depth++;
    if (line.match(/^\S/)) depth = 0;
  }
  return code.substring(start, endRecent);
}

// Check step_nm_confirm differences (it showed 10.9% size increase)
console.log('\n=== KEY FUNCTION COMPARISON: step_nm_confirm ===');
const v1NmConfirm = findFuncFull(files.main, 'step_nm_confirm');
const v2NmConfirm = findFuncFull(files.handlers, 'step_nm_confirm');
console.log('V1 step_nm_confirm first 600 chars:');
console.log(v1NmConfirm ? v1NmConfirm.substring(0, 600) : 'NOT FOUND');
console.log('\nV2 step_nm_confirm first 600 chars:');
if (v2NmConfirm) {
  console.log(v2NmConfirm.substring(0, 600));
} else {
  const v2_alt = findFuncFull(files.init, 'step_nm_confirm');
  console.log(v2_alt ? v2_alt.substring(0, 600) : 'NOT FOUND in handlers or init');
}

// Check the referral code additions in V2
console.log('\n=== V2 referral code functions ===');
const refCodeV2 = findFuncFull(files.init, 'fetch_referral_code');
if (refCodeV2) console.log('fetch_referral_code:\n' + refCodeV2.substring(0, 600));
const saveRefV2 = findFuncFull(files.init, 'save_referral_code');
if (saveRefV2) console.log('save_referral_code:\n' + saveRefV2.substring(0, 600));

// Check _replit_delete
console.log('\n=== V2 _replit_delete ===');
const rdel = findFuncFull(files.init, '_replit_delete');
if (rdel) console.log(rdel.substring(0, 600));

// Check check_disc_session_conflict
console.log('\n=== V2 check_disc_session_conflict ===');
const discConf = findFuncFull(files.init, 'check_disc_session_conflict');
if (discConf) console.log(discConf.substring(0, 800));

// Check fetch_promotions_cached
console.log('\n=== V2 fetch_promotions_cached ===');
const promoCache = findFuncFull(files.init, 'fetch_promotions_cached');
if (promoCache) console.log(promoCache.substring(0, 800));
