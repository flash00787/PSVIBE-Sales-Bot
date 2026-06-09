const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const files = [
  '/root/psvibe_api_server/app.py',
  '/root/psvibe-sales-bot/bot/console.py',
  '/root/psvibe-sales-bot/bot/sales.py',
  '/root/psvibe-sales-bot/bot/__init__.py',
  '/root/psvibe-sales-bot/bot/api_client.py',
];

const outDir = '/home/node/.openclaw/workspace/.tmp/vps_files';
fs.mkdirSync(outDir, { recursive: true });

const conn = new Client();

conn.on('ready', () => {
  console.log('Connected!');
  let pending = files.length;

  files.forEach((file) => {
    const basename = path.basename(file, path.extname(file));
    const ext = path.extname(file);
    let filename = basename + ext;
    // disambiguate __init__.py
    if (basename === '__init__') {
      filename = 'bot_init.py';
    }
    if (basename === 'api_client') {
      filename = 'api_client.py';
    }

    conn.exec(`cat "${file}"`, (err, stream) => {
      if (err) {
        console.error(`Error reading ${file}:`, err.message);
        pending--;
        if (pending === 0) conn.end();
        return;
      }
      let data = '';
      stream.on('data', (chunk) => { data += chunk.toString(); });
      stream.stderr.on('data', (chunk) => { console.error(`stderr ${file}:`, chunk.toString()); });
      stream.on('close', (code) => {
        if (code === 0) {
          const outPath = path.join(outDir, filename);
          fs.writeFileSync(outPath, data);
          console.log(`Wrote ${file} -> ${outPath} (${data.length} bytes)`);
        } else {
          console.error(`Non-zero exit ${code} for ${file}`);
          const outPath = path.join(outDir, filename);
          fs.writeFileSync(outPath, `EXIT CODE ${code}\n${data}`);
        }
        pending--;
        if (pending === 0) conn.end();
      });
    });
  });
});

conn.on('error', (err) => {
  console.error('SSH error:', err.message);
  process.exit(1);
});

conn.connect({
  host: HOST,
  username: USER,
  privateKey: fs.readFileSync(KEY_PATH),
  readyTimeout: 15000,
});
