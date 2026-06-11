const fs = require('fs');
const path = require('path');
const Client = require('ssh2').Client;

const CONFIG = {
  host: '5.223.81.16',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000,
};

async function uploadFile(localPath, remotePath) {
  const content = fs.readFileSync(localPath);
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.exec('cat > ' + remotePath, (err, stream) => {
        if (err) { reject(err); return; }
        stream.stdin.write(content);
        stream.stdin.end();
        let out = '';
        stream.on('data', d => out += d);
        stream.stderr.on('data', d => out += d);
        stream.on('close', () => { conn.end(); resolve(out); });
      });
    });
    conn.on('error', reject);
    conn.connect(CONFIG);
  });
}

async function execCmd(cmd) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { reject(err); return; }
        let out = '';
        stream.on('data', d => out += d);
        stream.stderr.on('data', d => out += d);
        stream.on('close', () => { conn.end(); resolve(out); });
      });
    });
    conn.on('error', reject);
    conn.connect(CONFIG);
  });
}

async function main() {
  // 1. Create remote dir
  await execCmd('mkdir -p /opt/ibet789-bot');
  
  // 2. Upload files
  const files = [
    'package.json',
    'config.js',
    'bot.js',
    '.env.example',
    'ibet789-bot.service',
    'README.md',
  ];
  
  for (const f of files) {
    const localPath = path.join('/home/node/.openclaw/workspace/ibet789-bot', f);
    if (fs.existsSync(localPath)) {
      await uploadFile(localPath, '/opt/ibet789-bot/' + f);
      console.log('Uploaded:', f);
    }
  }
  
  // 3. Install npm packages
  console.log('Installing npm packages (Chromium download ~300MB)...');
  const result = await execCmd('cd /opt/ibet789-bot && npm install puppeteer node-telegram-bot-api dotenv 2>&1 | tail -10');
  console.log('NPM result:', result.substring(0, 500));
  
  // 4. Create deploy.sh
  await uploadFile(
    path.join('/home/node/.openclaw/workspace/ibet789-bot', 'deploy.sh'),
    '/opt/ibet789-bot/deploy.sh'
  );
  await execCmd('chmod +x /opt/ibet789-bot/deploy.sh');
  
  // 5. Create systemd service
  const serviceContent = await execCmd('cat /opt/ibet789-bot/ibet789-bot.service');
  console.log('Service file:', serviceContent.substring(0, 200));
  
  console.log('Deployment complete!');
  console.log('Next: Edit /opt/ibet789-bot/.env with BOT_TOKEN and agent credentials');
}

main().catch(e => console.error('Error:', e.message));
