#!/usr/bin/env node
// PS VIBE V2 — Add missing _replit_patch function
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
  console.log('🔧 PS VIBE V2 — Add _replit_patch\n');

  // Check the refactored backup __init__ for _replit_patch
  await sshRun("grep -n '_replit_patch' /root/Sales-Tele-Bot_refactored/__init___refactored.py | head -5", '_replit_patch in __init___refactored.py');

  // Show lines around _replit_delete in __init__.py to know where to insert
  await sshRun("grep -n '_replit_delete\\|_replit_patch\\|_api_base\\|_load_cfg' /root/Sales-Tele-Bot_refactored/bot/__init__.py", 'Context around _replit_delete');

  // Now insert _replit_patch after _replit_delete
  // Use sed to insert after the closing of _replit_delete function
  // _replit_delete ends at line 1449 (based on earlier output, line 1435-1449 area)
  // Let's find the exact line
  await sshRun("sed -n '1435,1460p' /root/Sales-Tele-Bot_refactored/bot/__init__.py", 'Lines 1435-1460');

  console.log('\n✅ DONE');
}

main().catch(err => { console.error('FATAL:', err); process.exit(1); });
