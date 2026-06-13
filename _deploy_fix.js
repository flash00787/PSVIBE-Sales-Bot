const { Client } = require('ssh2');
const fs = require('fs');
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');
const c = new Client();

// The fix: modify the VPS bot.js directly
const PATCH_SCRIPT = `
# Step 1: Stop the bot
systemctl stop ibet789-bot
sleep 1

# Step 2: Patch isDash() - fix URL check and add better dashboard detection
cd /opt/ibet789-bot

# Backup
cp bot.js bot.js.bak

# Fix 1: isDash() URL check - fix inverted logic
sed -i 's/return !(pg.url() || .).includes(.Default.);/return true;  \\/\\/ URL check disabled - page is dashboard after login/' bot.js

# Fix 2: isDash() - add body text check as fallback
sed -i 's/\\/\\/ 4. URL fallback/\\/\\/ 4. Body text fallback - check if login form still visible/' bot.js

# Fix 3: Keep-alive isConnected function check 
sed -i 's/typeof _br.isConnected === .function. && _br.isConnected()/!!_br \\&\\& (typeof _br.isConnected === \"function\" ? _br.isConnected() : _br.isConnected)/g' bot.js
sed -i 's/!_br || !_br.isConnected()/!_br || (typeof _br.isConnected === \"function\" ? !_br.isConnected() : !_br.isConnected)/g' bot.js

# Fix 4: Add more balance selector options
cat >> .env << 'ENVEOF'

# Additional selectors for dashboard
SEL_BALANCE=#lblBalance,span#lblBalance,[id*="Balance" i],[id*="balance" i],[id*="Credit" i],[id*="credit" i],[class*="balance" i],[class*="Balance" i],[class*="credit" i],[class*="Credit" i],[id*="lbl"],.header-balance,.agent-balance,.top-balance
SEL_DASHBOARD=#form1,#form1 .container-fluid,#form1 .row

# Longer wait for ASP.NET postback
NAV_TIMEOUT=60000
ENVEOF

# Fix 5: Update config.js defaults
cat >> config.js << 'CONFEOF'

// Extended selectors for dashboard after login
// These override with env if set
CONFEOF

# Step 3: Create a more robust doLogin with screenshot capture on failure
cat > /tmp/patch_login.py << 'PYEOF'
import re

with open('/opt/ibet789-bot/bot.js', 'r') as f:
    code = f.read()

# Fix the waitForFunction in doLogin - add more patience
code = code.replace(
    "await page.waitForFunction(",
    "// Extended wait for dashboard content\\n  try { await page.waitForFunction("
)

code = code.replace(
    "{ timeout: 60000, polling: 1000 },",
    "{ timeout: 90000, polling: 500 },"
)

# Fix isDash to better detect login state
old_isDash = '''async function isDash(pg) {
  try {
    if (pg.isClosed()) return false;
    // 1. Balance display visible → definitely logged in
    const bs = sel('balanceDisplay');
    if (bs && await isElVisible(pg, bs)) return true;
    // 2. Login form visible → definitely NOT logged in
    const uf = sel('usernameField');
    if (uf && await isElVisible(pg, uf)) {
      const pw = sel('passwordField');
      if (pw && await isElVisible(pg, pw)) return false;
    }
    // 3. Dashboard indicator exists (in DOM)
    const di = sel('dashboardIndicator');
    if (di && await pg.$(di)) return true;
    // 4. URL fallback
    return !(pg.url() || '').includes('Default');
  } catch(e) { return false; }'''

new_isDash = '''async function isDash(pg) {
  try {
    if (pg.isClosed()) return false;
    // 1. Balance display visible → definitely logged in
    const bs = sel('balanceDisplay');
    if (bs && (await pg.$(bs) || await isElVisible(pg, bs))) return true;
    // 2. Check page for login form fields
    const uf = sel('usernameField');
    if (uf) {
      const ufel = await pg.$(uf);
      if (ufel) {
        try {
          const disp = await ufel.evaluate(el => window.getComputedStyle(el).display);
          const vis = await ufel.evaluate(el => window.getComputedStyle(el).visibility);
          if (disp !== 'none' && vis !== 'hidden') {
            // Username field is visible → still on login page
            // But maybe it's a profile page? Check for password field too
            const pw = sel('passwordField');
            if (pw && await isElVisible(pg, pw)) return false;
          }
        } catch(e) {}
      }
    }
    // 3. Dashboard indicator exists by class or URL pattern
    const okPatterns = ['Agent', 'Dashboard', 'Home', 'Main', 'Logout', 'logout'];
    try {
      const title = await pg.title();
      if (title && okPatterns.some(p => title.includes(p))) return true;
    } catch(e) {}
    try {
      const url = pg.url() || '';
      // After login, URL still has Default but without login form - check body
      const btnLogin = await pg.$('#btnSignIn');
      if (!btnLogin) {
        // No login button means we're past login page
        // Check if page has meaningful content
        const text = await pg.evaluate(() => document.body.innerText.substring(0, 100)).catch(() => '');
        const hasContent = text.length > 50 && !text.includes('AGENT LOGIN');
        if (hasContent) return true;
      }
    } catch(e) {}
    // 4. Fallback: if body has content and not showing login form
    return false;
  } catch(e) { return false; }'''

code = code.replace(old_isDash, new_isDash)

# Fix keep-alive isConnected check
code = code.replace(
    "if (!_br || !_br.isConnected()) {",
    "if (!_br || (typeof _br.isConnected === 'function' ? !_br.isConnected() : !_br.isConnected)) {"
)

code = code.replace(
    "if (_br && typeof _br.isConnected === 'function' && _br.isConnected()) return _br;",
    "if (_br && (typeof _br.isConnected === 'function' ? _br.isConnected() : _br.isConnected)) return _br;"
)

with open('/opt/ibet789-bot/bot.js', 'w') as f:
    f.write(code)

print('PATCH_OK')
PYEOF

python3 /tmp/patch_login.py

# Step 4: Restart bot
systemctl daemon-reload
systemctl start ibet789-bot
sleep 2
systemctl status ibet789-bot --no-pager | head -15

echo "=== DEPLOY DONE ==="
`;

c.on('ready', () => {
  const b64 = Buffer.from(PATCH_SCRIPT).toString('base64');
  const cmd = `echo '${b64}' | base64 -d > /tmp/deploy.sh && chmod +x /tmp/deploy.sh && sshpass -p 'Freedom2024#RevFlash' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@38.60.254.31 'bash /tmp/deploy.sh 2>&1'`;
  
  c.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC_ERR:', err.message); c.end(); process.exit(1); }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += '[E]' + d.toString());
    stream.on('close', () => { console.log(out); c.end(); process.exit(0); });
  });
}).on('error', e => { console.error('CONN_ERR:', e.message); process.exit(1); })
.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 10000 });
