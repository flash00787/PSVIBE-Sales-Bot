const { Client } = require('ssh2');
const fs = require('fs');
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');
const c = new Client();

// The Python script - written to main VPS and executed
// Uses %% to avoid Python indentation issues in heredoc
const pyScript = `import subprocess, base64, sys

pw = "Freedom2024#RevFlash"
remote = "38.60.254.31"
ssh_cmd = ["sshpass", "-p", pw, "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", f"root@{remote}"]
scp_cmd = ["sshpass", "-p", pw, "scp", "-o", "StrictHostKeyChecking=no"]

# Read bot.js
result = subprocess.run(ssh_cmd + ["cat /opt/ibet789-bot/bot.js.bak5"], capture_output=True, text=True, timeout=15)
code = result.stdout
orig = code

# Apply fixes
fixes = []

# Fix 1: Replace entire waitForFunction block with simple wait
# Find markers
old_wait_block = """  try {
    await page.waitForFunction(
      (s) => {
        const el = document.querySelector(s);
        if (!el) return false;
        const st = window.getComputedStyle(el);
        return st.display !== 'none' && st.visibility !== 'hidden' && el.offsetParent !== null;
      },
      { timeout: 120000, polling: 300 },
      balSel
    );
    console.log('[L] Login OK (balance visible)');
    _pg = page; _lt = Date.now(); return page;
  } catch(e) {
    console.log('[L] waitForFunction err:', (e.message || '').substring(0,60));
  }"""

new_wait_block = """  // Simple wait for ASP.NET postback
  console.log('[L] Waiting 20s for postback...');
  await new Promise(r => setTimeout(r, 20000));
  
  // Check if login succeeded - look for login form elements
  try {
    const hasLoginForm = await page.evaluate(() => {
      const el = document.querySelector('#txtUserName');
      if (!el) return false;
      return el.offsetParent !== null;
    });
    if (!hasLoginForm) {
      console.log('[L] Login OK');
      _pg = page; _lt = Date.now(); return page;
    }
  } catch(e) {}
  
  // Additional wait for form to disappear
  console.log('[L] Waiting extra 20s...');
  for (let i = 0; i < 20; i++) {
    await new Promise(r => setTimeout(r, 1000));
    try {
      const el = await page.evaluate(() => document.querySelector('#txtUserName') !== null);
      if (!el) {
        console.log('[L] Login OK (form gone)');
        _pg = page; _lt = Date.now(); return page;
      }
    } catch(e) {}
  }
  console.log('[!] Login FAILED. URL:', await page.evaluate(() => location.href).catch(()=>'?'));"""

if old_wait_block in code:
    code = code.replace(old_wait_block, new_wait_block)
    fixes.append("login_wait")
else:
    fixes.append("LOGIN_WAIT_MISSING")

# Fix 2: Remove screenshot section    
old_screenshot = """  // Capture what went wrong
  console.log('[!] Login failed. Taking snapshot...');
  try {
    const sp = await page.screenshot({encoding:'base64', fullPage:false});
    fs.writeFileSync('/tmp/login_fail_snap.txt', sp);
    const url = page.url();
    const ttl = await page.title().catch(() => '?');
    const body = await page.evaluate(() => document.body.innerHTML.substring(0,800)).catch(() => 'NO ACCESS');
    console.log('[!] URL:', url, 'Title:', ttl);
    console.log('[!] Body:', body);
  } catch(se) { console.log('[!] Snap err:', (se.message || '').substring(0,40)); }"""

new_screenshot = """  // Login failed - just throw
  console.log('[!] Login failed');"""

if old_screenshot in code:
    code = code.replace(old_screenshot, new_screenshot)
    fixes.append("screenshot")
else:
    fixes.append("SCREENSHOT_MISSING")

# Fix 3: Remove fallback loop (now handled by our new wait logic)
old_fallback = """  // Fallback: quick check
  console.log('[L] Fallback check...');
  const fpURL = page.url();
  const fpTitle = await page.title().catch(() => '?');
  console.log('[L] URL after login:', fpURL);
  console.log('[L] Title:', fpTitle);
  try {
    const inputs = await page.evaluate(() => { return document.querySelectorAll('input').length; });
    console.log('[L] Input count:', inputs);
  } catch(e) {}
  for (let i = 0; i < 30; i++) {
    await new Promise(r => setTimeout(r, 1000));
    try {
      if (await isDash(page)) {
        console.log('[L] Login OK (fallback)');
        _pg = page; _lt = Date.now(); return page;
      }
    } catch(e) {}
  }"""

if old_fallback in code:
    code = code.replace(old_fallback, "")
    fixes.append("fallback_removed")
else:
    fixes.append("FALLBACK_MISSING")

if code != orig:
    # Write patched file
    open("/tmp/yangon_bot_patched.js", "w").write(code)
    encoded = base64.b64encode(code.encode()).decode()
    print(f"PATCHED: {','.join(fixes)}")
    print(f"SIZE: {len(code)} bytes")
    print(f"B64: {encoded[:40]}...")
    
    # Transfer and restart
    write_cmd = ssh_cmd + [f"cat > /opt/ibet789-bot/bot.js << 'B64EOF'\\n{encoded}\\nB64EOF"]
    subprocess.run(ssh_cmd + [f"systemctl stop ibet789-bot"], timeout=10)
    subprocess.run(ssh_cmd + [f"echo '{encoded}' | base64 -d > /opt/ibet789-bot/bot.js"], timeout=15)
    subprocess.run(ssh_cmd + [f"systemctl start ibet789-bot"], timeout=10)
    r = subprocess.run(ssh_cmd + ["sleep 3; systemctl is-active ibet789-bot; echo LOGS; journalctl -u ibet789-bot --no-pager -n 15"], capture_output=True, text=True, timeout=30)
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[:500])
else:
    print("NO_CHANGES")`;

c.on('ready', () => {
  const b64Script = Buffer.from(pyScript).toString('base64');
  const cmd = `echo '${b64Script}' | base64 -d > /tmp/final_fix.py && python3 /tmp/final_fix.py 2>&1`;
  
  c.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC_ERR:', err.message); c.end(); process.exit(1); }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += '[E]' + d.toString());
    stream.on('close', (code) => { console.log(out); c.end(); process.exit(code || 0); });
  });
}).on('error', e => { console.error('CONN_ERR:', e.message); process.exit(1); })
.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 10000 });
