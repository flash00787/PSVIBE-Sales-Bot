const { Client } = require('ssh2');
const fs = require('fs');

const c = new Client();
c.on('ready', () => {
  console.log('Connected to Yangon VPS');
  
  c.exec('cat /opt/ibet789-bot/bot.js 2>&1', (err, stream) => {
    if (err) { console.error('ERR:', err.message); process.exit(1); }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += '[E]' + d.toString());
    stream.on('close', () => {
      let code = out;
      const orig = code;
      const fixes = [];

      // Find the exact block boundaries by line number
      const lines = code.split('\n');
      let waitStart = -1, waitEnd = -1, throwEnd = -1;

      for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes("console.log('[L] Waiting for balance element:")) {
          waitStart = i;
        }
        if (waitStart > 0 && waitEnd < 0 && lines[i].includes("'[L] Login FAILED'")) {
          waitEnd = i;
        }
        if (waitEnd > 0 && lines[i].includes("throw new Error('Login failed')")) {
          throwEnd = i;
          break;
        }
      }

      console.log('Block boundaries: waitStart=' + waitStart + ' waitEnd=' + waitEnd + ' throwEnd=' + throwEnd);

      if (waitStart > 0 && waitEnd > 0) {
        // Calculate the exact replacement text
        const oldBlock = lines.slice(waitStart, waitEnd + 1).join('\n');
        
        const newBlock = [
          "  // Wait for ASP.NET postback (login form disappears)",
          "  console.log('[L] Waiting for postback...');",
          "  try {",
          "    await page.waitForSelector('#txtUserName', { timeout: 25000, visible: true });",
          "    console.log('[L] Form still visible...');",
          "  } catch(e) {",
          "    console.log('[L] Login OK (form gone)');",
          "    _pg = page; _lt = Date.now(); return page;",
          "  }",
          "  try {",
          "    await page.waitForSelector('#txtUserName', { timeout: 25000, visible: true });",
          "  } catch(e) {",
          "    console.log('[L] Login OK');",
          "    _pg = page; _lt = Date.now(); return page;",
          "  }",
          "  console.log('[!] Login FAILED');",
        ].join('\n');

        if (code.includes(oldBlock)) {
          code = code.replace(oldBlock, newBlock);
          fixes.push('wait_block');
        } else {
          fixes.push('WAIT_BLOCK_MISMATCH');
          console.log('TEXT MISMATCH. First 100 chars of oldBlock:', oldBlock.substring(0, 100));
        }
      }

      // Replace the throw line if needed
      if (throwEnd > 0) {
        const oldThrow = lines[throwEnd];
        if (oldThrow !== "  throw new Error('Login failed');") {
          lines[throwEnd] = "  throw new Error('Login failed');";
          code = lines.join('\n');
          fixes.push('throw_line');
        }
      }

      if (code !== orig) {
        const b64 = Buffer.from(code).toString('base64');
        // Use a file write approach to avoid # in bash
        c.exec('cat > /opt/ibet789-bot/bot.js', { exec: { pty: false } }, (e2, s2) => {
          if (e2) { console.error('WRITE_ERR:', e2.message); process.exit(1); }
          s2.stdin.write(Buffer.from(code, 'utf8'));
          s2.stdin.end();
          s2.on('close', () => {
            c.exec('systemctl restart ibet789-bot && sleep 3 && echo STATUS && systemctl is-active ibet789-bot', (e3, s3) => {
              let o3=''; s3.on('data',d=>o3+=d); s3.stderr.on('data',d=>o3+='[E]'+d); s3.on('close',()=>{
                console.log('DONE:', o3, 'FIXES:', fixes.join(','));
                process.exit(0);
              });
            });
          });
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
