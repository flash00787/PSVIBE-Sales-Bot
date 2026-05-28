#!/usr/bin/env node
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
  console.log('🔍 FINAL VERIFICATION\n');

  // 1. Check main_menu.py
  await sshRun('cd /root/staging/bot_src && python3 -c "import ast; ast.parse(open(\'bot/handlers/main_menu.py\').read()); print(\'OK\')"', '1. main_menu.py staging');
  await sshRun('cd /root/Sales-Tele-Bot_refactored && python3 -c "import ast; ast.parse(open(\'bot/handlers/main_menu.py\').read()); print(\'OK\')"', '1. main_menu.py refactored');

  // 2. keep_alive.py
  await sshRun("ls -la /root/staging/bot_src/keep_alive.py /root/Sales-Tele-Bot_refactored/keep_alive.py 2>&1", '2. keep_alive.py exists');

  // 3. __init__.py syntax
  await sshRun('cd /root/staging/bot_src && python3 -c "import ast; ast.parse(open(\'bot/handlers/__init__.py\').read()); print(\'OK\')"', '3. __init__.py staging');
  await sshRun('cd /root/Sales-Tele-Bot_refactored && python3 -c "import ast; ast.parse(open(\'bot/handlers/__init__.py\').read()); print(\'OK\')"', '3. __init__.py refactored');

  // 4. Duplicate dirs cleaned
  await sshRun("ls -d /root/staging/bot_src/bot/bot/ /root/staging/bot_src/handlers/ /root/Sales-Tele-Bot_refactored/bot/bot/ /root/Sales-Tele-Bot_refactored/handlers/ 2>&1 || echo 'All clean'", '4. Duplicate dirs');

  // 5. app.py duplicates
  await sshRun("ls /root/Sales-Tele-Bot_refactored/app.py /root/staging/bot_src/app.py 2>&1 || echo 'All clean'", '5. app.py duplicates');

  // 6. _replit_patch exists
  await sshRun("grep -c '_replit_patch' /root/Sales-Tele-Bot_refactored/bot/__init__.py /root/staging/bot_src/bot/__init__.py", '6. _replit_patch count');

  // 7. All __init__.py syntax
  await sshRun('cd /root/Sales-Tele-Bot_refactored && python3 -c "import ast; ast.parse(open(\'bot/__init__.py\').read()); print(\'OK\')"', '7. bot/__init__.py refactored');
  await sshRun('cd /root/staging/bot_src && python3 -c "import ast; ast.parse(open(\'bot/__init__.py\').read()); print(\'OK\')"', '7. bot/__init__.py staging');

  // 8. Final cross-check - missing functions
  await sshRun("comm -23 <(grep -ohP '(?<=def )\\\\w+' /root/staging/monolithic_ref/main.py | sort -u) <(grep -rohP '(?<=def )\\\\w+' /root/Sales-Tele-Bot_refactored/ --include='*.py' | sort -u)", '8. Remaining missing functions');

  // 9. Show _replit_delete + _replit_patch context
  await sshRun("grep -n 'def _replit' /root/Sales-Tele-Bot_refactored/bot/__init__.py", '9. _replit functions');

  console.log('\n✅ FINAL VERIFICATION COMPLETE');
}

main().catch(err => { console.error('FATAL:', err); process.exit(1); });
