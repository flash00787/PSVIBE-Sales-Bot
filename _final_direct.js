const { Client } = require('ssh2');
const fs = require('fs');

const c = new Client();
c.on('ready', () => {
  console.log('[OK] Connected to Yangon VPS');
  
  // Read current bot.js
  c.exec('cat /opt/ibet789-bot/bot.js.bak5 2>&1', (err, stream) => {
    if (err) { console.error('ERR:', err.message); process.exit(1); }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += '[E]' + d.toString());
    stream.on('close', () => {
      let code = out;
      const orig = code;
      const fixes = [];
      
      // Fix 1: Replace the entire login wait block  
      const OLD_WAIT = [
        "  // Simple wait for ASP.NET postback",
        "  console.log('[L] Waiting 20s for page...');",
        "  await new Promise(r => setTimeout(r, 20000));",
        "  ",
        "  // Check if login form is gone",
        "  try {",
        "    const hasLogin = await page.evaluate(() => {",
        "      const u = document.querySelector('#txtUserName');",
        "      return u !== null && u.offsetParent !== null;",
        "    });",
        "    if (!hasLogin) {",
        "      console.log('[L] Login OK');",
        "      _pg = page; _lt = Date.now(); return page;",
        "    }",
        "  } catch(e) {}",
        "",
      ].join('\n');
      
      const NEW_WAIT = [
        "  // Wait for login form to disappear (ASP.NET postback)",
        "  console.log('[L] Waiting for postback...');",
        "  try {",
        "    await page.waitForSelector('#txtUserName', { timeout: 20000, visible: true });",
        "    console.log('[L] Form still visible, trying more...');",
        "  } catch(e) {",
        "    // Timeout = form not visible = login worked",
        "    console.log('[L] Login OK (form gone)');",
        "    _pg = page; _lt = Date.now(); return page;",
        "  }",
        "  // Wait more",
        "  try {",
        "    await page.waitForSelector('#txtUserName', { timeout: 20000, visible: true });",
        "  } catch(e) {",
        "    console.log('[L] Login OK');",
        "    _pg = page; _lt = Date.now(); return page;",
        "  }",
        "  console.log('[L] Postback may have failed');",
      ].join('\n');
      
      if (code.includes(OLD_WAIT)) {
        code = code.replace(OLD_WAIT, NEW_WAIT);
        fixes.push('wait_block');
      } else {
        fixes.push('WAIT_MISSING');
      }
      
      // Fix 2: Replace pg with page in fallback
      const OLD_FB = "if ((await pg.$('#btnSignIn')) === null && (await pg.$('#txtUserName')) === null) {";
      const NEW_FB = "if ((await page.$('#txtUserName')) === null) {";
      if (code.includes(OLD_FB)) {
        code = code.replace(OLD_FB, NEW_FB);
        fixes.push('pg_fallback');
      } else {
        fixes.push('PG_MISSING');
      }
      
      // Fix 3: Remove screenshot section
      const OLD_SS = [
        "  // Capture what went wrong",
        "  console.log('[!] Login failed after ' + (i+1) + ' seconds. Taking snapshot...');",
        "  try {",
        "    const sp = await page.screenshot({encoding:'base64', fullPage:false});",
        "    fs.writeFileSync('/tmp/login_fail_snap.txt', sp);",
        "    const url = page.url();",
        "    const ttl = await page.title().catch(() => '?');",
        "    const body = await page.evaluate(() => document.body.innerHTML.substring(0,800)).catch(() => 'NO ACCESS');",
        "    console.log('[!] URL:', url, 'Title:', ttl);",
        "    console.log('[!] Body:', body);",
        "  } catch(se) { console.log('[!] Snap err:', (se.message || '').substring(0,40)); }",
      ].join('\n');
      const NEW_SS = [
        "  console.log('[!] Login FAILED');",
      ].join('\n');
      if (code.includes(OLD_SS)) {
        code = code.replace(OLD_SS, NEW_SS);
        fixes.push('screenshot');
      } else {
        fixes.push('SS_MISSING');
      }
      
      // Fix 4: Fallback 'i' reference error (line 226 uses i+1 but i is out of scope)
      // Already fixed by removing the whole screenshot block
      
      if (code !== orig) {
        // Write fixed file back
        const b64 = Buffer.from(code).toString('base64');
        c.exec('echo ' + b64 + ' | base64 -d > /opt/ibet789-bot/bot.js && systemctl stop ibet789-bot; sleep 1; systemctl start ibet789-bot; echo DONE', (e, s) => {
          let o=''; s.on('data',d=>o+=d); s.stderr.on('data',d=>o+='[E]'+d); s.on('close',()=>{console.log('DEPLOY:', o, '| FIXES:', fixes.join(',')); process.exit(0);});
        });
      } else {
        console.log('NO_CHANGES. Fixes attempted:', fixes.join(','));
        process.exit(0);
      }
    });
  });
}).on('error', e => { console.error('CONN_ERR:', e.message); process.exit(1); })
.connect({
  host: '38.60.254.31',
  port: 22,
  username: 'root',
  password: 'Freedom2024#RevFlash',
  readyTimeout: 15000
});
