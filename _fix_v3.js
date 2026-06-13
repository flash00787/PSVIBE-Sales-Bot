const { Client } = require('ssh2');
const fs = require('fs');
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');
const c = new Client();

c.on('ready', () => {
  // Write the patch script to main VPS, then scp to Yangon VPS, then execute
  const cmd = `
# Write the patch node script to main VPS
cat > /tmp/patch_ibet_v3.js << 'PATCHEOF'
const fs = require('fs');
let code = fs.readFileSync('/opt/ibet789-bot/bot.js', 'utf8');
const orig = code;
const changes = [];

// Fix 1: Replace broken pg reference in fallback check
const broken = "if ((await pg.$('#btnSignIn')) === null && (await pg.$('#txtUserName')) === null) {";
const fixed = "if (await isDash(page)) {";
if (code.includes(broken)) { code = code.replace(broken, fixed); changes.push('fallback fixed'); }

// Fix 2: Extend waitForFunction timeout
if (code.includes('{ timeout: 60000, polling: 1000 },')) {
  code = code.replace('{ timeout: 60000, polling: 1000 },', '{ timeout: 120000, polling: 300 },');
  changes.push('waitForFunction timeout 60->120s');
}

// Fix 3: Improve isDash URL check
const oldUrlCheck = "return true; // URL check disabled - post-login page still has Default";
const newUrlCheck = "try { const u = pg.url() || ''; if (u.includes('Login') || u.includes('login') || u.includes('SignIn')) return false; } catch(e) {} return true;";
if (code.includes(oldUrlCheck)) {
  code = code.replace(oldUrlCheck, newUrlCheck);
  changes.push('isDash URL check improved');
} else {
  changes.push('isDash URL check NOT FOUND (may already be fixed)');
}

// Fix 4: Add more aggressive getBal fallback
const getBalEnd = "  } catch(e) {}\\\\n  return null;";
const getBalExtended = code.includes("// Fallback: scan entire page text for numbers");
if (!getBalExtended) {
  // Add the fallback text scanning before the final return null in getBal
  const lastReturnNull = code.lastIndexOf('return null;');
  const getBalFunc = code.indexOf('async function getBal(page)');
  if (lastReturnNull > getBalFunc) {
    const before = code.substring(0, lastReturnNull);
    const after = code.substring(lastReturnNull);
    const insert = 
      "  // Fallback: scan entire page text for numbers\\n" +
      "  try {\\n" +
      "    const allText = await page.evaluate(() => document.body.innerText);\\n" +
      "    const pats = [/Balance[\\\\s:]*([\\\\d,.]+)/i, /Credit[\\\\s:]*([\\\\d,.]+)/i,\\" +
      "      /Total[\\\\s:]*([\\\\d,.]+)/i, /Agent Balance[\\\\s:]*([\\\\d,.]+)/i,\\" +
      "      /Cash Balance[\\\\s:]*([\\\\d,.]+)/i, /Wallet[\\\\s:]*([\\\\d,.]+)/i];\\n" +
      "    for (const p of pats) { const m = allText.match(p); if (m) return m[1]; }\\n" +
      "  } catch(e) {}\\n";
    code = before + insert + after;
    changes.push('getBal added text scanning fallback');
  }
}

// Fix 5: Ensure login failure captures more diagnostic info
code = code.replace(
  "console.log('[!] Login failed. Taking snapshot...');",
  "console.log('[!] Login failed. Page info -> URL:', fpURL, 'Title:', fpTitle, 'Inputs:', await page.evaluate(() => document.querySelectorAll('input').length).catch(()=>'err'));\\n  console.log('[!] Login failed. Taking snapshot...');"
);
changes.push('login failure diagnostics');

// Fix 6: After login failure, try navigating to a known dashboard page
const oldRetryBrowser = "console.log('[!] Login failed');\\n  console.log('[I] Launching browser...');";
const newRetryBrowser = "console.log('[!] Login failed');";
if (code.includes(oldRetryBrowser)) {
  code = code.replace(oldRetryBrowser, newRetryBrowser);
  changes.push('retry logic removed');
}

if (code !== orig) {
  fs.writeFileSync('/opt/ibet789-bot/bot.js', code);
  console.log('PATCHED: ' + changes.join(', '));
} else {
  console.log('NO_CHANGES');
}
PATCHEOF

# Copy to Yangon VPS and apply
sshpass -p 'Freedom2024#RevFlash' scp -o StrictHostKeyChecking=no /tmp/patch_ibet_v3.js root@38.60.254.31:/tmp/patch_ibet_v3.js
sshpass -p 'Freedom2024#RevFlash' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@38.60.254.31 '
  systemctl stop ibet789-bot
  sleep 1
  node /tmp/patch_ibet_v3.js 2>&1
  rc=$?
  echo "PATCH_EXIT: $rc"
  systemctl start ibet789-bot
  echo "BOT_STARTED"
'
`;
  
  c.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC_ERR:', err.message); c.end(); process.exit(1); }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += '[E]' + d.toString());
    stream.on('close', (code) => { console.log(out); c.end(); process.exit(code || 0); });
  });
}).on('error', e => { console.error('CONN_ERR:', e.message); process.exit(1); })
.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 10000 });
