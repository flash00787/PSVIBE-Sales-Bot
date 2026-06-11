const fs = require('fs');
const Client = require('ssh2').Client;

const SSH_CONFIG = {
  host: '5.223.81.16',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000,
};

function runCmd(cmd) {
  return new Promise((resolve, reject) => {
    const c = new Client();
    c.on('ready', () => {
      c.exec(cmd, (e, s) => {
        if (e) { reject(e); return; }
        let o = '';
        s.on('data', d => o += d);
        s.stderr.on('data', d => o += d);
        s.on('close', () => { c.end(); resolve(o); });
      });
    });
    c.on('error', reject);
    c.connect(SSH_CONFIG);
  });
}

function writeFile(remotePath, content) {
  return new Promise((resolve, reject) => {
    const c = new Client();
    c.on('ready', () => {
      c.exec('cat > ' + remotePath, (e, s) => {
        if (e) { reject(e); return; }
        s.stdin.write(content);
        s.stdin.end();
        let o = '';
        s.on('data', d => o += d);
        s.stderr.on('data', d => o += d);
        s.on('close', () => { c.end(); resolve(o); });
      });
    });
    c.on('error', reject);
    c.connect(SSH_CONFIG);
  });
}

(async () => {
  try {
    // 1. Update config.js on workspace first, then upload
    let configCode = fs.readFileSync('/home/node/.openclaw/workspace/ibet789-bot/config.js', 'utf8');
    configCode = configCode.replace(
      'PUPPETEER_HEADLESS: process.env.PUPPETEER_HEADLESS !== \'false\',',
      `PUPPETEER_HEADLESS: process.env.PUPPETEER_HEADLESS !== 'false',

  // Proxy server for geo-restricted access (e.g., Myanmar proxy)
  PROXY_SERVER: process.env.PROXY_SERVER || '',`
    );
    fs.writeFileSync('/home/node/.openclaw/workspace/ibet789-bot/config.js', configCode);
    await writeFile('/opt/ibet789-bot/config.js', configCode);
    console.log('config.js updated ✅');

    // 2. Update bot.js
    let botCode = fs.readFileSync('/home/node/.openclaw/workspace/ibet789-bot/bot.js', 'utf8');
    
    // Fix browser.isConnected bug
    botCode = botCode.replace(
      'const browser = await getBrowser();',
      'browser = await getBrowser();'
    );
    console.log('Fixed browser.isConnected bug ✅');

    // Add proxy support
    botCode = botCode.replace(
      `args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--disable-web-security',
      '--disable-features=IsolateOrigins,site-per-process',
    ],`,
      `args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--disable-web-security',
      '--disable-features=IsolateOrigins,site-per-process',
      ...(config.PROXY_SERVER ? ['--proxy-server=' + config.PROXY_SERVER] : []),
    ],`
    );
    console.log('Added proxy support ✅');
    
    fs.writeFileSync('/home/node/.openclaw/workspace/ibet789-bot/bot.js', botCode);
    await writeFile('/opt/ibet789-bot/bot.js', botCode);
    console.log('bot.js uploaded ✅');

    // 3. Update .env with proxy
    let envData = await runCmd('cat /opt/ibet789-bot/.env');
    if (!envData.includes('PROXY_SERVER=')) {
      // Remove existing AGENT_URL lines that are broken, add clean ones
      let lines = envData.split('\n').filter(l => !l.startsWith('AGENT…'));
      lines.push('AGENT_URL=https://ag.108sode.com');
      lines.push('');
      lines.push('# Proxy for geo-restricted sites');
      lines.push('PROXY_SERVER=');
      await writeFile('/opt/ibet789-bot/.env', lines.join('\n'));
    }
    
    // Verify
    const check = await runCmd('grep -E "AGENT_URL=|PROXY_SERVER=" /opt/ibet789-bot/.env');
    console.log('Env check:\n' + check);
    
    // 4. Restart
    await runCmd('systemctl restart ibet789-bot');
    await new Promise(r => setTimeout(r, 2000));
    const logs = await runCmd('journalctl -u ibet789-bot --no-pager -n 4');
    console.log('Bot restarted:\n' + logs);
    
    console.log('\n✅ All fixes applied!');
    console.log('⚠️ Boss needs to provide a Myanmar proxy server to bypass geo-blocking.');
    
  } catch(e) {
    console.error('Error:', e.message);
  }
})();
