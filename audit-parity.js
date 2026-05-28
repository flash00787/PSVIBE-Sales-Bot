const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();

const VPS = {
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
};

function execCommand(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let output = '';
      let errOutput = '';
      stream.on('data', d => output += d.toString());
      stream.stderr.on('data', d => errOutput += d.toString());
      stream.on('close', code => {
        if (code !== 0) reject(new Error(`Exit ${code}: ${errOutput || output}`));
        else resolve(output);
      });
    });
  });
}

async function main() {
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect(VPS);
  });

  console.log('Connected to VPS');

  // Read files
  const files = {
    v1: '/root/Aung Chan Myint/Sales-Tele-Bot/main.py',
    v2_init: '/root/Aung Chan Myint/Sales-Tele-Bot/bot/__init__.py',
    v2_app: '/root/Aung Chan Myint/Sales-Tele-Bot/bot/app.py',
    v2_handlers: '/root/Aung Chan Myint/Sales-Tele-Bot/bot/handlers.py'
  };

  for (const [key, filepath] of Object.entries(files)) {
    try {
      const content = await execCommand(conn, `cat "${filepath}"`);
      fs.writeFileSync(`/tmp/audit_${key}.py`, content);
      console.log(`Read ${key}: ${content.length} chars`);
    } catch (e) {
      console.log(`Error reading ${key}: ${e.message}`);
    }
  }

  // Get line counts
  for (const [key, filepath] of Object.entries(files)) {
    try {
      const lines = await execCommand(conn, `wc -l "${filepath}"`);
      console.log(`${key} lines: ${lines.trim()}`);
    } catch (e) {}
  }

  conn.end();
}

main().catch(e => { console.error(e); process.exit(1); });
