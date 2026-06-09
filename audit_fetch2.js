const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();
const OUT = '/home/node/.openclaw/workspace/vps_files/';

try { fs.mkdirSync(OUT, {recursive:true}); } catch(e) {}

conn.on('ready', () => {
  console.log('SSH CONNECTED');

  // Files to fetch
  const files = [
    '/root/Sales-Tele-Bot/.env',
    '/root/Sales-Tele-Bot/.env.example',
    '/root/Sales-Tele-Bot/requirements.txt',
    '/root/Sales-Tele-Bot/main.py',
    '/root/Sales-Tele-Bot/bot/__init__.py',
    '/root/Sales-Tele-Bot/bot/app.py',
    '/root/Sales-Tele-Bot/bot/handlers.py',
    '/root/Sales-Tele-Bot/start.sh',
    '/root/Sales-Tele-Bot/update_bot.sh',
  ];

  let idx = 0;
  function fetchNext() {
    if (idx >= files.length) {
      console.log('DONE ALL. Now fetch customer_bot.py...');
      // Fetch customer_bot.py separately (it's big)
      const rpath = '/root/Sales-Tele-Bot/customer_bot.py';
      const lpath = OUT + 'customer_bot.py';
      conn.sftp((err, sftp) => {
        if (err) { console.error('SFTP err', err); conn.end(); return; }
        sftp.fastGet(rpath, lpath, (err2) => {
          if (err2) console.error('fastGet err:', err2);
          else console.log('Fetched customer_bot.py, size:', fs.statSync(lpath).size);
          conn.end();
        });
      });
      return;
    }
    const rpath = files[idx];
    const fname = rpath.replace(/\//g, '_').replace(/^_root_Sales-Tele-Bot_/, '');
    const lpath = OUT + fname;
    idx++;
    conn.exec('cat ' + rpath, (err, stream) => {
      if (err) { console.error('exec err:', err, rpath); fetchNext(); return; }
      let out = '';
      stream.on('data', d => out += d.toString());
      stream.stderr.on('data', d => {});
      stream.on('close', () => {
        try { fs.writeFileSync(lpath, out); console.log('Saved:', fname, out.length, 'bytes'); } catch(e) { console.error('write err:', e.message); }
        fetchNext();
      });
    });
  }
  fetchNext();
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err);
  process.exit(1);
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  password: 'Freedom2024#RevFlash',
  readyTimeout: 15000,
});
