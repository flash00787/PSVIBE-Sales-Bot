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
  // Show exact line with _load_cfg
  await sshRun("grep -n '_load_cfg' /root/Sales-Tele-Bot_refactored/bot/__init__.py", 'Lines with _load_cfg');
  
  // Show lines 1448-1455
  await sshRun("sed -n '1448,1455p' /root/Sales-Tele-Bot_refactored/bot/__init__.py", 'Lines 1448-1455');

  // Hex dump to see exact characters
  await sshRun("sed -n '1452p' /root/Sales-Tele-Bot_refactored/bot/__init__.py | xxd | head -5", 'Hex dump line 1452');
}

main().catch(err => { console.error('FATAL:', err); process.exit(1); });
