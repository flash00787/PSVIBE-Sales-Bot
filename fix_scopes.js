const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  // Fix: Remove update_inv_total_k1 from scopes and reset
  const cmds = [
    'echo "=== Fixing scopes in __init__.py ==="',
    // Remove scope corruption
    'sed -n "/^SCOPES\\|_replit_get\\|_replit_post\\|def ensure_sheet/=" /root/Sales-Tele-Bot_refactored/bot/__init__.py | head -5',
    '',
    'echo "---",
    // Show what SCOPES currently looks like
    'grep -n "SCOPES" /root/Sales-Tele-Bot_refactored/bot/__init__.py',
    '',
    'echo "---",
    // Fix: replace the corrupted line - SCOPES should only be 3 scopes
    'grep "^SCOPES" /root/Sales-Tele-Bot_refactored/bot/__init__.py',
  ].join(' && ');
  c.exec(cmds, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
