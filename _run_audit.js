const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const VPS = '5.223.81.16';
const KEY = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const V2 = '/root/Sales-Tele-Bot_refactored';
const V1 = '/root/staging/monolithic_ref';
const OUT = '/home/node/.openclaw/workspace';

function ssh(cmd) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let out = '';
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { conn.end(); reject(err); return; }
        stream.on('data', d => out += d.toString());
        stream.stderr.on('data', d => out += d.toString());
        stream.on('close', () => { conn.end(); resolve(out.trim()); });
      });
    }).on('error', e => { conn.end(); reject(e); })
    .connect({
      host: VPS, username: 'root',
      privateKey: fs.readFileSync(KEY),
      readyTimeout: 30000
    });
  });
}

function writeFile(name, content) {
  fs.writeFileSync(path.join(OUT, name), content);
  console.log(`  WROTE: ${name}`);
}

(async () => {
  console.log('=== A1: FILE TREE ===');
  let tree = await ssh(`cd ${V2} && find . -name '*.py' -not -path '*/__pycache__/*' | sort`);
  writeFile('A1_filetree.txt', tree);
  let pyCount = tree.split('\n').filter(l=>l.trim()).length;
  console.log(`  Python files: ${pyCount}`);

  let dupes = await ssh(`cd ${V2} && echo "bot/bot/:"; ls -la bot/bot/ 2>&1; echo "---"; echo "handlers/:"; ls -la handlers/ 2>&1; echo "---"; echo "app.py:"; ls -la app.py 2>&1; echo "---"; echo "keep_alive.py:"; ls -la keep_alive.py 2>&1`);
  writeFile('A1_duplicates.txt', dupes);

  // syntax check via Python ast
  let syntax = await ssh(`cd ${V2} && python3 << 'PYEOF'
import ast, os, sys
errs=[]
for r,ds,fs in os.walk('.'):
  if '__pycache__' in r: continue
  for f in fs:
    if not f.endswith('.py'): continue
    fp=os.path.join(r,f)
    try:
      with open(fp) as h: ast.parse(h.read())
    except SyntaxError as e:
      errs.append(f'{fp}: {e}')
if errs:
  for e in errs: print(e)
else:
  print('ALL FILES PASS SYNTAX CHECK')
PYEOF`);
  writeFile('A1_syntax.txt', syntax);
  console.log(`  Syntax: ${syntax.includes('ALL FILES') ? 'ALL PASS ✅' : 'ERRORS FOUND ❌'}`);

  let starImports = await ssh(`cd ${V2} && grep -rn "from bot import *" bot/ --include='*.py'`);
  writeFile('A1_starimports.txt', starImports || 'NONE FOUND');
  let starCount = starImports ? starImports.split('\n').filter(l=>l.trim()).length : 0;
  console.log(`  from bot import * count: ${starCount}`);

  let allExport = await ssh(`cd ${V2} && grep -A50 "__all__" bot/__init__.py | head -60`);
  writeFile('A1_export_all.txt', allExport);

  console.log('');
  console.log('=== A2: FUNCTION PARITY ===');
  let v1f = await ssh(`cd ${V1} && grep -n "^def \\|^async def " main.py`);
  writeFile('A2_v1_functions.txt', v1f);
  let v1c = v1f.split('\n').filter(l=>l.trim()).length;
  console.log(`  V1 functions: ${v1c}`);

  let v2f = await ssh(`cd ${V2} && grep -rn "^def \\|^async def " bot/ --include='*.py'`);
  writeFile('A2_v2_functions.txt', v2f);
  let v2c = v2f.split('\n').filter(l=>l.trim()).length;
  console.log(`  V2 functions: ${v2c}`);

  let critical = await ssh(`cd ${V2} && for fn in now_mmt today_str step_hdr calc_duration _sheets_retry fetch_allowed_staff_ids _int _pin_then _replit_get _replit_post _replit_patch _replit_delete _api_base; do echo -n "$fn: "; grep -rn "def $fn" bot/ --include='*.py' | head -1 || echo "MISSING"; done`);
  writeFile('A2_critical.txt', critical);
  console.log(`  Critical helpers: ${critical.split('\n').filter(l=>l.includes('MISSING')).length} missing`);

  console.log('');
  console.log('=== A3: STATES ===');
  let stateCount = await ssh(`cd ${V2} && grep -c "= auto()" bot/__init__.py 2>/dev/null || echo 0`);
  writeFile('A3_state_count.txt', stateCount);
  console.log(`  BotState count: ${stateCount}`);

  let appStates = await ssh(`cd ${V2} && grep -n "ConversationHandler\\|entry_points\\|states\\|fallbacks" bot/app.py`);
  writeFile('A3_app_states.txt', appStates || 'NONE');
  
  let stateList = await ssh(`cd ${V2} && grep "= auto()" bot/__init__.py 2>/dev/null | head -30`);
  writeFile('A3_state_list.txt', stateList);

  console.log('');
  console.log('=== A4: DEAD CODE ===');
  let sqlite = await ssh(`cd ${V2} && echo "=== sqlite/ exists? ==="; ls -la sqlite/ 2>&1; echo "=== referenced? ==="; grep -rn "sqlite\\|db_manager\\|PSVibeDB" bot/ --include='*.py' 2>/dev/null || echo "NO REFERENCES"`);
  writeFile('A4_sqlite.txt', sqlite);
  console.log(`  SQLite dead code: ${sqlite.includes('sqlite') && !sqlite.includes('NO REFERENCES') ? 'CHECK' : 'NOT REFERENCED'}`);

  let deadImports = await ssh(`cd ${V2} && grep -rn "^import \\|^from " bot/handlers/ --include='*.py' | grep -v "__future__\\|telegram\\|os\\|json\\|time\\|re\\|datetime\\|random\\|threading\\|asyncio\\|functools\\|typing"`);
  writeFile('A4_unusual_imports.txt', deadImports || 'NONE');

  let envCheck = await ssh(`cd ${V2} && ls -la .env 2>&1`);
  writeFile('A4_env_file.txt', envCheck);

  console.log('');
  console.log('=== A5: SECURITY ===');
  let secrets = await ssh(`cd ${V2} && grep -rn "sk-\\|xai-\\|sk-or\\|api_key" bot/ --include='*.py' | grep -v "os.environ\\|environ.get\\|__all__\\|# ignore" | grep -v "^.*#" || echo "NO HARDCODED SECRETS"`);
  writeFile('A5_secrets.txt', secrets);

  let auth = await ssh(`cd ${V2} && grep -B2 -A10 "TypeHandler\\|group=-999\\|auth\\|fetch_allowed_staff" bot/app.py | head -40`);
  writeFile('A5_auth.txt', auth);

  let errorH = await ssh(`cd ${V2} && grep -A20 "async def error_handler" bot/handlers/help.py`);
  writeFile('A5_error_handler.txt', errorH);

  let service = await ssh(`cat /etc/systemd/system/psvibe-bot-refactored.service 2>/dev/null || echo "NOT FOUND"`);
  writeFile('A5_service.txt', service);

  let processes = await ssh(`ps aux | grep python | grep -v grep`);
  writeFile('A5_processes.txt', processes);

  console.log('');
  console.log('========================================');
  console.log('  ALL 5 AUDITS COMPLETE');
  console.log(`  V1 funcs: ${v1c} | V2 funcs: ${v2c}`);
  console.log(`  Syntax: ${syntax.includes('ALL FILES') ? '✅' : '❌'}`);
  console.log(`  Star imports: ${starCount} files`);
  console.log(`  Critical helpers missing: ${critical.split('\n').filter(l=>l.includes('MISSING')).length}`);
  console.log('========================================');
})();
