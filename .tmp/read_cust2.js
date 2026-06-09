const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const files = [
  '/root/psvibe-sales-bot/customer_bot/api.py',
  '/root/psvibe-sales-bot/customer_bot/main.py',
  '/root/psvibe-sales-bot/customer_bot/__init__.py',
  '/root/psvibe-sales-bot/customer_bot/handlers.py',
];

const outDir = '/home/node/.openclaw/workspace/.tmp/vps_files_cust';
const fs2 = require('fs');
fs2.mkdirSync(outDir, { recursive: true });

const conn = new Client();
conn.on('ready', () => {
  let pending = files.length;
  files.forEach((f) => {
    const name = f.split('/').pop();
    conn.exec(`cat "${f}"`, (err, stream) => {
      let data = '';
      stream.on('data', (chunk) => { data += chunk.toString(); });
      stream.on('close', (code) => {
        fs2.writeFileSync(`${outDir}/${name}`, data);
        console.log(`Wrote ${name} (${data.length} bytes, exit=${code})`);
        pending--;
        if (pending === 0) conn.end();
      });
    });
  });
});
conn.on('error', (err) => { console.error('Error:', err.message); });
conn.connect({ host: HOST, username: 'root', privateKey: fs.readFileSync(KEY_PATH), readyTimeout: 20000 });
