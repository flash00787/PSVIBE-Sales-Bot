const { Client } = require('ssh2');
const fs = require('fs');
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');
const c = new Client();

const patchCode = `
const fs = require('fs');
let code = fs.readFileSync('/opt/ibet789-bot/bot.js', 'utf8');
const orig = code;
const changes = [];

// Fix 1: isDash URL check - inverted logic
const oldUrlCheck = "return !(pg.url() || '').includes('Default');";
const newUrlCheck = "// URL check: page stays at Default1.aspx after login, so check login form presence instead\\n    return true;";
if (code.includes(oldUrlCheck)) {
  code = code.replace(oldUrlCheck, newUrlCheck);
  changes.push('isDash URL check fixed');
}

// Fix 2: ensureBrowser isConnected
const oldBrCheck1 = "if (_br && typeof _br.isConnected === 'function' && _br.isConnected()) return _br;";
const newBrCheck1 = "try { if (_br) { if (typeof _br.isConnected === 'function' && _br.isConnected()) return _br; if (_br.isConnected) return _br; } } catch(e) { _br = null; _pg = null; _lt = null; }";
if (code.includes(oldBrCheck1)) {
  code = code.replace(oldBrCheck1, newBrCheck1);
  changes.push('ensureBrowser isConnected');
}

// Fix 3: keep-alive isConnected
const oldKeepAlive = "if (!_br || !_br.isConnected()) {";
const newKeepAlive = "if (!_br || (typeof _br.isConnected === 'function' ? !_br.isConnected() : !_br.isConnected)) {";
if (code.includes(oldKeepAlive)) {
  code = code.replace(oldKeepAlive, newKeepAlive);
  changes.push('keepAlive isConnected');
}

// Fix 4: status isConnected
const oldStatusCheck = "brOK = _br && typeof _br.isConnected === 'function' && _br.isConnected();";
const newStatusCheck = "try { brOK = _br && (typeof _br.isConnected === 'function' ? _br.isConnected() : !!_br.isConnected); } catch(e) { brOK = false; }";
if (code.includes(oldStatusCheck)) {
  code = code.replace(oldStatusCheck, newStatusCheck);
  changes.push('status isConnected');
}

// Fix 5: Extend fallback loop from 15 to 30 iterations
code = code.replace("for (let i = 0; i < 15; i++) {", "for (let i = 0; i < 30; i++) {");
changes.push('fallback loop 15->30');

// Fix 6: Add more console logging during login failures
const oldSnapLog = "console.log('[!] Login failed. Taking snapshot...');";
const newSnapLog = "console.log('[!] Login failed after ' + (i+1) + ' seconds. Taking snapshot...');";
if (code.includes(oldSnapLog)) {
  code = code.replace(oldSnapLog, newSnapLog);
}

// Fix 7: Better balance extraction - try page text regex first too
const oldGetBalReturn = "if (txt) return txt;";
const newGetBalReturn = "if (txt && txt.length > 0 && !txt.includes('__')) return txt;";
if (code.includes(oldGetBalReturn)) {
  code = code.replace(oldGetBalReturn, newGetBalReturn);
  changes.push('getBal empty check');
}

// Fix 8: Ensure browser launch at startup handles failures gracefully
const oldPreLaunch = "console.log('[I] Pre-launching Chrome...');";
const newPreLaunch = "console.log('[I] Pre-launching Chrome...');\\n      await new Promise(r => setTimeout(r, 1000));";
if (code.includes(oldPreLaunch)) {
  code = code.replace(oldPreLaunch, newPreLaunch);
}

// Fix 9: After login failure, don't keep trying - detect the post-login page content better
const oldFallbackCheck = "if (await isDash(page)) {";
// Count occurrences - we want the one in doLogin, not ensure
// Find all occurrences and replace carefully
const lines = code.split('\\n');
let foundInDoLogin = false;
for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('Fallback check...')) {
    foundInDoLogin = true;
    continue;
  }
  if (foundInDoLogin && lines[i].includes('if (await isDash(page)) {')) {
    lines[i] = "      if ((await pg.$('#btnSignIn')) === null && (await pg.$('#txtUserName')) === null) {";
    changes.push('fallback login detection');
    break;
  }
}
code = lines.join('\\n');

if (code !== orig) {
  fs.writeFileSync('/opt/ibet789-bot/bot.js', code);
  console.log('PATCHED: ' + changes.join(', '));
} else {
  console.log('NO_CHANGES (code unchanged)');
}
`;

c.on('ready', () => {
  const b64 = Buffer.from(patchCode).toString('base64');
  const cmd = `echo '${b64}' | base64 -d > /tmp/ibet_patch2.js && sshpass -p 'Freedom2024#RevFlash' scp -o StrictHostKeyChecking=no /tmp/ibet_patch2.js root@38.60.254.31:/tmp/ibet_patch2.js && sshpass -p 'Freedom2024#RevFlash' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@38.60.254.31 'systemctl stop ibet789-bot; sleep 1; node /tmp/ibet_patch2.js 2>&1; systemctl start ibet789-bot; sleep 3; journalctl -u ibet789-bot --no-pager -n 20 2>&1'`;

  c.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC_ERR:', err.message); c.end(); process.exit(1); }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += '[E]' + d.toString());
    stream.on('close', () => { console.log(out); c.end(); process.exit(0); });
  });
}).on('error', e => { console.error('CONN_ERR:', e.message); process.exit(1); })
.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 10000 });
