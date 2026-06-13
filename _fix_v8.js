const { Client } = require('ssh2');
const fs = require('fs');

const c = new Client();
c.on('ready', () => {
  console.log('Connecting...');
  
  // Read from remote and apply inline fix  
  c.exec('cat /opt/ibet789-bot/bot.js 2>&1', (err, stream) => {
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += '[E]' + d.toString());
    stream.on('close', () => {
      let code = out;
      const orig = code;
      const fixes = [];
      
      // Replace the waitForFunction block with waitForSelector
      const oldBlock = `  const balSel = sel('balanceDisplay');
  console.log('[L] Waiting for balance element:', balSel);
  try {
    await page.waitForFunction(
      (s) => {
        const el = document.querySelector(s);
        if (!el) return false;
        const st = window.getComputedStyle(el);
        return st.display !== 'none' && st.visibility !== 'hidden' && el.offsetParent !== null;
      },
      { timeout: 60000, polling: 1000 },
      balSel
    );
    console.log('[L] Login OK (balance visible)');
    _pg = page; _lt = Date.now(); return page;
  } catch(e) {
    console.log('[L] waitForFunction err:', (e.message || '').substring(0,40));
  }`;
      
      const newBlock = `  // Wait for login form to disappear (ASP.NET postback)
  console.log('[L] Waiting for postback...');
  try {
    await page.waitForSelector('#txtUserName', { timeout: 25000, visible: true });
    console.log('[L] Form still visible...');
  } catch(e) {
    console.log('[L] Login OK (form gone)');
    _pg = page; _lt = Date.now(); return page;
  }
  try {
    await page.waitForSelector('#txtUserName', { timeout: 25000, visible: true });
  } catch(e) {
    console.log('[L] Login OK');
    _pg = page; _lt = Date.now(); return page;
  }
  console.log('[L] Postback wait over');`;
      
      if (code.includes(oldBlock)) {
        code = code.replace(oldBlock, newBlock);
        fixes.push('wait_block');
        console.log('WAIT_BLOCK_REPLACED');
      } else {
        fixes.push('WAIT_BLOCK_MISSING');
        console.log('WAIT_BLOCK_MISSING');
        // Show what we're looking for vs what's there
        console.log('Looking for:', oldBlock.substring(0, 60));
      }
      
      if (code !== orig) {
        // Write back via stdin pipe
        c.exec('cat > /opt/ibet789-bot/bot.js', { exec: { pty: false } }, (e2, s2) => {
          if (e2) { console.error('WRITE_ERR:', e2.message); process.exit(1); }
          s2.stdin.write(Buffer.from(code, 'utf8'));
          s2.stdin.end();
          s2.on('close', () => {
            c.exec('systemctl restart ibet789-bot && echo DONE', (e3, s3) => {
              let o3=''; s3.on('data',d=>o3+=d); s3.stderr.on('data',d=>o3+='[E]'+d); s3.on('close',()=>{
                console.log('FIXES:', fixes.join(','));
                console.log('RESTART:', o3);
                process.exit(0);
              });
            });
          });
        });
      } else {
        console.log('NO_CHANGES');
        process.exit(0);
      }
    });
  });
}).on('error', e => { console.error('ERR:', e.message); process.exit(1); })
.connect({ host: '38.60.254.31', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000 });
