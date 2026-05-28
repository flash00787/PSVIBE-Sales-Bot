#!/usr/bin/env node
// PS VIBE V2 — Additional fixes
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
  console.log('🔧 PS VIBE V2 — Additional fixes...\n');

  // ─────────────────────────────────────
  // A. Check _replit_patch in V1
  // ─────────────────────────────────────
  console.log('📋 [A] Find _replit_patch in V1...');
  await sshRun("grep -n '_replit_patch\\|def _replit_patch' /root/staging/monolithic_ref/main.py | head -20", 'V1 _replit_patch');

  // ─────────────────────────────────────
  // B. Check _replit_patch references in V2 that would break
  // ─────────────────────────────────────
  console.log('📋 [B] _replit_patch usage in V2...');
  await sshRun("grep -rn '_replit_patch' /root/Sales-Tele-Bot_refactored/ --include='*.py' 2>/dev/null", 'V2 _replit_patch refs');

  // ─────────────────────────────────────
  // C. Check _update_inv_total_k1 in V1
  // ─────────────────────────────────────
  console.log('📋 [C] Find _update_inv_total_k1 in V1...');
  await sshRun("grep -n '_update_inv_total_k1' /root/staging/monolithic_ref/main.py | head -20", 'V1 _update_inv_total_k1');

  // ─────────────────────────────────────
  // D. Check _update_inv_total_k1 in V2
  // ─────────────────────────────────────
  console.log('📋 [D] _update_inv_total_k1 in V2...');
  await sshRun("grep -rn '_update_inv_total_k1' /root/Sales-Tele-Bot_refactored/ --include='*.py' 2>/dev/null || echo 'NOT_FOUND'", 'V2 _update_inv_total_k1 refs');

  // ─────────────────────────────────────
  // E. Check keep_alive.py exists at both locations
  // ─────────────────────────────────────
  console.log('📋 [E] Verify keep_alive.py exists...');
  await sshRun("ls -la /root/staging/bot_src/keep_alive.py 2>/dev/null && echo 'STAGING: EXISTS' || echo 'STAGING: NOT_FOUND'", 'Staging keep_alive');
  await sshRun("ls -la /root/Sales-Tele-Bot_refactored/keep_alive.py 2>/dev/null && echo 'REFACTORED: EXISTS' || echo 'REFACTORED: NOT_FOUND'", 'Refactored keep_alive');

  // ─────────────────────────────────────
  // F. Get V1 _replit_patch full function
  // ─────────────────────────────────────
  console.log('📋 [F] Extract V1 _replit_patch function...');
  await sshRun("sed -n '/^def _replit_patch/,/^def /p' /root/staging/monolithic_ref/main.py | head -30", 'V1 _replit_patch func');

  // ─────────────────────────────────────
  // G. Get V1 _update_inv_total_k1
  // ─────────────────────────────────────
  console.log('📋 [G] Extract V1 _update_inv_total_k1...');
  await sshRun("grep -n '_update_inv_total_k1' /root/staging/monolithic_ref/main.py", 'V1 _update_inv_total_k1 lines');
  
  console.log('\n✅ DONE');
}

main().catch(err => { console.error('FATAL:', err); process.exit(1); });
