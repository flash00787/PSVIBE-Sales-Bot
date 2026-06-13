const { Client } = require('ssh2');
const fs = require('fs');
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');
const c = new Client();

// The patch Node.js code - simple replacements only, no complex patterns
const patchCode = [
  "const fs = require('fs');",
  "let c = fs.readFileSync('/opt/ibet789-bot/bot.js', 'utf8');",
  "let o = c; let f = [];",
  "",
  // Fix 1: Replace the entire waitForFunction + fallback + screenshot section
  // in doLogin with simple URL-based detection
  "const oldLoginWait = \"  try {\\n    await page.waitForFunction(\" +",
  "      \"\\n      (s) => {\" +",
  "      \"\\n        const el = document.querySelector(s);\" +",
  "      \"\\n        if (!el) return false;\" +",
  "      \"\\n        const st = window.getComputedStyle(el);\" +",
  "      \"\\n        return st.display !== 'none' && st.visibility !== 'hidden' && el.offsetParent !== null;\" +",
  "      \"\\n      },\" +",
  "      \"\\n      { timeout: 120000, polling: 300 },\" +",
  "      \"\\n      balSel\" +",
  "      \"\\n    );\" +",
  "      \"\\n    console.log('[L] Login OK (balance visible)');\" +",
  "      \"\\n    _pg = page; _lt = Date.now(); return page;\" +",
  "      \"\\n  } catch(e) {\" +",
  "      \"\\n    console.log('[L] waitForFunction err:', (e.message || '').substring(0,60));\" +",
  "      \"\\n  }\";",
  "",
  "const newLoginWait = [",
  "  '  // Wait for URL to change after ASP.NET postback',",
  "  '  const urlBefore = page.url();',",
  "  '  console.log(\\\"[L] Waiting for postback...\\\");',",
  "  '  for (let i = 0; i < 20; i++) {',",
  "  '    await new Promise(r => setTimeout(r, 1000));',",
  "  '    try {',",
  "  '      const urlNow = page.url();',",
  "  '      if (urlNow !== urlBefore) {',",
  "  '        console.log(\\\"[L] URL changed to:\\\", urlNow);',",
  "  '        _pg = page; _lt = Date.now();',",
  "  '        console.log(\\\"[L] Login OK\\\");',",
  "  '        return page;',",
  "  '      }',",
  "  '    } catch(e) {}',",
  "  '  }',",
  "  '  // If URL didn\\\"'t change, check if login form is gone',",
  "  '  try {',",
  "  '    const hasLoginForm = await page.evaluate(() => document.querySelectorAll(\\\"#txtUserName:not([style*=none]):not([style*=hidden])\\\").length > 0);',",
  "  '    if (!hasLoginForm) {',",
  "  '      _pg = page; _lt = Date.now();',",
  "  '      console.log(\\\"[L] Login OK (form gone)\\\");',",
  "  '      return page;',",
  "  '    }',",
  "  '  } catch(e) {}',",
  "  '  // Give more time',",
  "  '  for (let i = 0; i < 20; i++) {',",
  "  '    await new Promise(r => setTimeout(r, 1000));',",
  "  '    try {',",
  "  '      if (!(await page.evaluate(() => document.querySelector(\\\"#txtUserName\\\") !== null))) {',",
  "  '        _pg = page; _lt = Date.now();',",
  "  '        console.log(\\\"[L] Login OK (txtUserName gone)\\\");',",
  "  '        return page;',",
  "  '      }',",
  "  '    } catch(e) {}',",
  "  '  }',",
  "].join('\\n');",
  "",
  "if (c.includes(oldLoginWait)) {",
  "  c = c.replace(oldLoginWait, newLoginWait);",
  "  f.push('login_wait');",
  "} else { f.push('login_wait_MISSING'); }",
  "",
  // Fix 2: Remove screenshot code (it hangs)
  "const oldSnapCode = [",
  "  \"  console.log('[!] Login failed. Taking snapshot...');\",",
  "  '  try {',",
  "  '    const sp = await page.screenshot({encoding:\\\"'base64\\\"', fullPage:false});',",
  "  '    fs.writeFileSync(\\\"'/tmp/login_fail_snap.txt\\\"', sp);',",
  "  '    const url = page.url();',",
  "  '    const ttl = await page.title().catch(() => \\\"'?\\\"');',",
  "  '    const body = await page.evaluate(() => document.body.innerHTML.substring(0,800)).catch(() => \\\"'NO ACCESS\\\"');',",
  "  '    console.log(\\\"'[!] URL:\\\"', url, \\\"'Title:\\\"', ttl);',",
  "  '    console.log(\\\"'[!] Body:\\\"', body);',",
  "  '  } catch(se) { console.log(\\\"'[!] Snap err:\\\"', (se.message || \\\"'\\\"').substring(0,40)); }',",
  "].join('\\n');",
  "const newSnapCode = \"  console.log('[!] Login failed. URL:', page.url(), 'Title:', await page.title().catch(()=>'?'));\";",
  "if (c.includes(oldSnapCode)) {",
  "  c = c.replace(oldSnapCode, newSnapCode);",
  "  f.push('snapshot');",
  "} else { f.push('snapshot_MISSING'); }",
  "",
  // Fix 3: Fix isConnected in status/browser checks
  // ensureBrowser: replace the isConnected line
  "c = c.replace(",
  "  'try { if (_br) { if (!!_br typeof _br.isConnected',",
  "  'try { if (_br) { if (typeof _br.isConnected === \"function\" ? _br.isConnected() : !!_br.isConnected)'",
  ");",
  "f.push('ensureBrowser');",
  "",
  // Fix 4: Keep-alive isConnected  
  "c = c.replace(",
  "  'if (!_br || !_br.isConnected()) {',",
  "  'if (!_br || (typeof _br.isConnected === \"function\" ? !_br.isConnected() : !_br.isConnected)) {',",
  ");",
  "f.push('keepAlive');",
  "",
  // Fix 5: status isConnected
  "c = c.replace(",
  "  'let brOK = false; try { brOK = _br && typeof _br.isConnected === \"function\" && _br.isConnected(); } catch(e) {}',",
  "  'let brOK = false; try { brOK = _br && (typeof _br.isConnected === \"function\" ? _br.isConnected() : !!_br.isConnected); } catch(e) {}',",
  ");",
  "f.push('status');",
  "",
  "if (c !== o) {",
  "  fs.writeFileSync('/opt/ibet789-bot/bot.js', c);",
  "  console.log('PATCHED: ' + f.join(', '));",
  "} else {",
  "  console.log('NO_CHANGES: ' + f.join(', '));",
  "}"
].join('\n');

c.on('ready', () => {
  const b64 = Buffer.from(patchCode).toString('base64');
  
  const cmds = [
    `echo '${b64}' | base64 -d > /tmp/patch_v6.js`,
    'sshpass -p Freedom2024#RevFlash scp -o StrictHostKeyChecking=no /tmp/patch_v6.js root@38.60.254.31:/tmp/patch_v6.js',
    'sshpass -p Freedom2024#RevFlash ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@38.60.254.31 \'cp /opt/ibet789-bot/bot.js.bak5 /opt/ibet789-bot/bot.js; systemctl stop ibet789-bot; sleep 1; node /tmp/patch_v6.js 2>&1; systemctl start ibet789-bot; sleep 3; echo STATUS; systemctl is-active ibet789-bot\''
  ].join(' && ');
  
  c.exec(cmds, (err, stream) => {
    if (err) { console.error('EXEC_ERR:', err.message); c.end(); process.exit(1); }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += '[E]' + d.toString());
    stream.on('close', (code) => { console.log(out); c.end(); process.exit(code || 0); });
  });
}).on('error', e => { console.error('CONN_ERR:', e.message); process.exit(1); })
.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 10000 });
