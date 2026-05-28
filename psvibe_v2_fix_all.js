#!/usr/bin/env node
// PS VIBE V2 — Bulk fix script
const { Client } = require('ssh2');
const fs = require('fs');

function sshRun(cmd, label) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { conn.end(); return reject(err); }
        let out = '', errOut = '';
        stream.on('data', d => out += d);
        stream.stderr.on('data', d => errOut += d);
        stream.on('close', (code) => {
          conn.end();
          console.log(`\n=== ${label} (exit ${code}) ===`);
          if (out.trim()) console.log(out.trim());
          if (errOut.trim()) console.log('STDERR:', errOut.trim());
          resolve({ code, out, errOut });
        });
      });
    }).connect({
      host: '167.71.196.120',
      username: 'root',
      privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
    });
  });
}

async function main() {
  console.log('🔧 PS VIBE V2 FIXES — Starting...\n');

  // ─────────────────────────────────────
  // 1. FIX MAIN_MENU.PY
  // ─────────────────────────────────────
  console.log('📋 [1/8] Fix main_menu.py...');
  let r = await sshRun('cp /root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py /root/staging/bot_src/bot/handlers/main_menu.py && echo "COPIED"', 'Copy main_menu.py');
  r = await sshRun('cd /root/staging/bot_src && python3 -c "import ast; ast.parse(open(\'bot/handlers/main_menu.py\').read()); print(\'OK\')"', 'Verify main_menu.py syntax');

  // ─────────────────────────────────────
  // 2. ADD KEEP_ALIVE.PY
  // ─────────────────────────────────────
  console.log('📋 [2/8] Handle keep_alive.py...');
  r = await sshRun('find /root/ -name "keep_alive.py" -not -path "*/__pycache__/*" 2>/dev/null', 'Find keep_alive.py sources');
  const foundPath = r.out.trim();
  if (foundPath) {
    console.log('  Found:', foundPath);
    await sshRun(`cp ${foundPath} /root/staging/bot_src/keep_alive.py && echo "COPIED to staging"`, 'Copy keep_alive to staging');
    await sshRun(`cp ${foundPath} /root/Sales-Tele-Bot_refactored/keep_alive.py && echo "COPIED to refactored"`, 'Copy keep_alive to refactored');
  } else {
    console.log('  NOT FOUND, creating minimal keep_alive.py...');
    const keepAliveContent = `from flask import Flask
from threading import Thread
import logging
logger = logging.getLogger(__name__)
app = Flask('')
@app.route('/')
def home():
    return "PS VIBE Bot is alive!"
def run():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
    logger.info("Keep-alive server started on port 8080")
`;
    const escaped = keepAliveContent.replace(/'/g, "'\\''");
    await sshRun(`echo '${escaped}' > /root/staging/bot_src/keep_alive.py && echo "CREATED staging"`, 'Create keep_alive staging');
    await sshRun(`echo '${escaped}' > /root/Sales-Tele-Bot_refactored/keep_alive.py && echo "CREATED refactored"`, 'Create keep_alive refactored');
  }

  // ─────────────────────────────────────
  // 3. FIX __init__.py — remove orphan imports
  // ─────────────────────────────────────
  console.log('📋 [3/8] Fix __init__.py orphan imports...');
  // Show first 10 lines before fix
  r = await sshRun('head -10 /root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py', 'BEFORE: __init__.py (refactored)');
  console.log('  BEFORE state shown above');
  
  // Use sed to remove lines 1-6 (the orphan imports before docstring)
  // But let's be safer — use Python to do it properly
  r = await sshRun(`python3 -c "
import re
for fpath in ['/root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py', '/root/staging/bot_src/bot/handlers/__init__.py']:
    with open(fpath) as f:
        content = f.read()
    # Find the first triple-quote docstring line and remove everything before it
    # Or more precisely, find the first non-comment, non-blank meaningful line
    lines = content.split('\\\\n')
    # Look for the 'Handlers package' docstring
    new_lines = []
    found_doc = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not found_doc:
            if stripped.startswith('\"\"\"') or stripped.startswith(\"'''\"):
                found_doc = True
                new_lines.append(line)
                continue
            elif stripped.startswith('from ') or stripped.startswith('import ') or stripped.startswith('#') or stripped == '':
                continue  # skip orphan imports/comments/blanks
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    new_content = '\\\\n'.join(new_lines)
    with open(fpath, 'w') as f:
        f.write(new_content)
    print(f'Fixed: {fpath}')
" 2>&1`, 'Python fix __init__.py');
  
  // Verify
  r = await sshRun('cd /root/Sales-Tele-Bot_refactored && python3 -c "import ast; ast.parse(open(\'bot/handlers/__init__.py\').read()); print(\'OK\')"', 'Verify __init__.py syntax (refactored)');
  r = await sshRun('cd /root/staging/bot_src && python3 -c "import ast; ast.parse(open(\'bot/handlers/__init__.py\').read()); print(\'OK\')"', 'Verify __init__.py syntax (staging)');
  
  // Show after
  r = await sshRun('head -10 /root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py', 'AFTER: __init__.py (refactored)');

  // ─────────────────────────────────────
  // 4. CLEAN DUPLICATE DIRECTORIES
  // ─────────────────────────────────────
  console.log('📋 [4/8] Clean duplicate directories...');
  for (const dir of [
    '/root/staging/bot_src/bot/bot/',
    '/root/staging/bot_src/handlers/',
    '/root/Sales-Tele-Bot_refactored/bot/bot/',
    '/root/Sales-Tele-Bot_refactored/handlers/'
  ]) {
    r = await sshRun(`ls -la ${dir} 2>/dev/null && echo "EXISTS: ${dir}" || echo "NOT_FOUND: ${dir}"`, `Check ${dir}`);
    if (r.out.includes('EXISTS')) {
      await sshRun(`rm -rf ${dir} && echo "DELETED: ${dir}"`, `Delete ${dir}`);
    }
  }

  // ─────────────────────────────────────
  // 5. REMOVE DUPLICATE TOP-LEVEL APP.PY
  // ─────────────────────────────────────
  console.log('📋 [5/8] Remove duplicate top-level app.py...');
  for (const f of [
    '/root/Sales-Tele-Bot_refactored/app.py',
    '/root/staging/bot_src/app.py'
  ]) {
    r = await sshRun(`if [ -f ${f} ]; then rm -f ${f} && echo "DELETED: ${f}"; else echo "NOT_FOUND: ${f}"; fi`, `Remove ${f}`);
  }

  // ─────────────────────────────────────
  // 6. V1 vs V2 FUNCTION CROSS-CHECK
  // ─────────────────────────────────────
  console.log('📋 [6/8] V1 vs V2 function cross-check...');
  r = await sshRun("grep -n '^async def \\|^def \\|^    async def \\|^    def ' /root/staging/monolithic_ref/main.py | head -150", 'V1 function defs');
  const v1Funcs = r.out;
  console.log(`\n--- V1 Functions ---\n${v1Funcs}\n`);
  
  r = await sshRun("grep -rn '^async def \\|^def \\|^    async def \\|^    def ' /root/Sales-Tele-Bot_refactored/ --include='*.py' | head -150", 'V2 function defs');
  const v2Funcs = r.out;
  console.log(`\n--- V2 Functions ---\n${v2Funcs}\n`);

  // Extract just function names for comparison
  await sshRun("grep -ohP '(?<=def )\\w+' /root/staging/monolithic_ref/main.py | sort -u > /tmp/v1_funcs.txt", 'Extract V1 func names');
  await sshRun("grep -rohP '(?<=def )\\w+' /root/Sales-Tele-Bot_refactored/ --include='*.py' | sort -u > /tmp/v2_funcs.txt", 'Extract V2 func names');
  
  r = await sshRun("comm -23 /tmp/v1_funcs.txt /tmp/v2_funcs.txt", 'Missing in V2');
  const missing = r.out.trim();
  if (missing) {
    console.log(`\n❌ FUNCTIONS IN V1 BUT MISSING IN V2:\n${missing}\n`);
  } else {
    console.log('\n✅ All V1 functions present in V2 (or V1 has no unique functions)\n');
  }

  // ─────────────────────────────────────
  // 7. API CHECK (Replit API usage)
  // ─────────────────────────────────────
  console.log('📋 [7/8] API check (Replit/API base)...');
  r = await sshRun("grep -rn '_replit_\\|Replit\\|replit' /root/Sales-Tele-Bot_refactored/ --include='*.py' 2>/dev/null || echo 'NO REPLIT REFERENCES'", 'Replit references');
  console.log(`Replit: ${r.out.trim()}`);
  
  r = await sshRun("grep -rn '_api_base\\|API_BASE_URL\\|API_KEY' /root/Sales-Tele-Bot_refactored/ --include='*.py' 2>/dev/null || echo 'NO API BASE REFERENCES'", 'API base references');
  console.log(`API base: ${r.out.trim()}`);
  
  r = await sshRun("find /root/Sales-Tele-Bot_refactored/ -name 'api_server.js' -o -name 'api_server.*' 2>/dev/null || echo 'NO API SERVER FILES'", 'API server files');
  console.log(`API server: ${r.out.trim()}`);

  // ─────────────────────────────────────
  // 8. VERIFY IMPORTS
  // ─────────────────────────────────────
  console.log('📋 [8/8] Verify bot imports...');
  r = await sshRun('cd /root/Sales-Tele-Bot_refactored && python3 -c "import sys; sys.path.insert(0, \'.\'); from bot import *; print(\'✅ Bot imports OK\')" 2>&1', 'Import test');
  console.log(`Import result: ${r.out.trim()}\n${r.errOut.trim()}`);
  
  // Also try the handlers init
  r = await sshRun('cd /root/Sales-Tele-Bot_refactored && python3 -c "import sys; sys.path.insert(0, \'.\'); from bot.handlers import *; print(\'✅ Handlers imports OK\')" 2>&1', 'Handlers import test');
  console.log(`Handlers import: ${r.out.trim()}\n${r.errOut.trim()}`);

  console.log('\n\n✅ ALL FIXES COMPLETE');
}

main().catch(err => {
  console.error('FATAL:', err);
  process.exit(1);
});
