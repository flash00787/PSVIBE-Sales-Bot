const { Client } = require('ssh2');
const fs = require('fs');
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

const c = new Client();
c.on('ready', async () => {
  console.log('[OK] Connected to main VPS');

  // Step 1: Create a diagnostic Puppeteer script on the Yangon VPS
  const diagScript = `
const pu = require('puppeteer');
(async () => {
  const b = await pu.launch({headless:'new', args:['--no-sandbox','--disable-dev-shm-usage']});
  const p = await b.newPage();
  await p.setDefaultNavigationTimeout(30000);
  
  console.log('NAVIGATING...');
  await p.goto('https://ag.108sode.com', {timeout:30000});
  await new Promise(r => setTimeout(r, 2000));
  
  // Pre-login page structure
  const pre = await p.evaluate(() => {
    const inputs = Array.from(document.querySelectorAll('input, button, select')).map(el => ({
      tag: el.tagName, id: el.id, name: el.name, type: el.type,
      placeholder: (el.placeholder||'').substring(0,20),
      value: (el.value||'').substring(0,20),
      className: (el.className||'').substring(0,30)
    }));
    const spans = Array.from(document.querySelectorAll('span[id], label[id], div[id]')).map(el => ({
      tag: el.tagName, id: el.id, text: (el.innerText||'').trim().substring(0,50)
    }));
    return { url: p.url(), title: document.title, inputs, spans: spans.slice(0,30) };
  });
  console.log('PRE_LOGIN:', JSON.stringify(pre));
  
  // Now login
  console.log('LOGGING IN...');
  await p.type('#txtUserName', 'jjacmc', {delay:50});
  await p.type('#txtPassword', 'WGZP202120@@@@', {delay:50});
  
  // Click login - ASP.NET postback
  await p.evaluate(() => document.getElementById('btnSignIn').click());
  
  // Wait for postback/dashboard to load
  console.log('WAITING...');
  await new Promise(r => setTimeout(r, 15000));
  
  // Post-login page structure
  const post = await p.evaluate(() => {
    const allEls = Array.from(document.querySelectorAll('*')).map(el => ({
      tag: el.tagName, id: el.id||'', cls: (el.className||'').substring(0,20),
      text: (el.innerText||'').trim().substring(0,40)
    })).filter(el => el.id || (el.cls && el.text));
    return { url: location.href, title: document.title, elements: allEls.slice(0,80) };
  });
  console.log('POST_LOGIN:', JSON.stringify(post));
  
  // Try more detailed scan of the dashboard
  const bodyHTML = await p.evaluate(() => {
    // Get ALL text content
    const text = document.body.innerText;
    const lines = text.split('\\n').filter(l => l.trim()).slice(0,30);
    // Count important elements
    const balSpans = Array.from(document.querySelectorAll('[id*="alance" i], [id*="redit" i], [class*="alance" i], [class*="redit" i], [id*="lbl"]'));
    const allSpans = Array.from(document.querySelectorAll('span[id], div[id], label[id]'));
    return { lines, balSpans: balSpans.map(s => s.outerHTML.substring(0,200)), allIds: allSpans.map(s => s.id).filter(Boolean) };
  });
  console.log('BODY:', JSON.stringify(bodyHTML));
  
  await b.close();
  console.log('DONE');
})();
`;
  
  // Write script to VPS then run it
  const escapedScript = diagScript.replace(/'/g, "'\\''");
  const cmd = `cat > /tmp/diag.js << 'SCRIPT_EOF'\n${diagScript}\nSCRIPT_EOF\ncd /opt/ibet789-bot && node /tmp/diag.js 2>&1`;
  
  const finalCmd = `sshpass -p 'Freedom2024#RevFlash' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@38.60.254.31 '${cmd}' 2>&1`;
  
  c.exec(finalCmd, (err, stream) => {
    if (err) { console.error('EXEC_ERR:', err.message); c.end(); process.exit(1); }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += '[E]' + d.toString());
    stream.on('close', () => { console.log(out); c.end(); process.exit(0); });
  });
}).on('error', e => { console.error('CONN_ERR:', e.message); process.exit(1); })
.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 10000 });
