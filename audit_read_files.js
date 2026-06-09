const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();
const keyPath = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const privateKey = fs.readFileSync(keyPath, 'utf8');

const files = {
  'api_client.py': '/root/agri/bot/api_client.py',
  'app.py': '/root/agri/bot/app.py',
  'booking.py': '/root/agri/bot/handlers/booking.py',
  'booking_flow.py': '/root/agri/bot/handlers/booking_flow.py',
  'stock.py': '/root/agri/bot/handlers/stock.py',
  'stock_in.py': '/root/agri/bot/handlers/stock_in.py',
  'referral.py': '/root/agri/bot/handlers/referral.py',
  'discount.py': '/root/agri/bot/handlers/discount.py',
  'waitlist.py': '/root/agri/bot/handlers/waitlist.py',
  'attendance.py': '/root/agri/bot/handlers/attendance.py',
  'broadcast.py': '/root/agri/bot/handlers/broadcast.py',
  'notify.py': '/root/agri/bot/handlers/notify.py',
  'games.py': '/root/agri/bot/handlers/games.py',
  'ssd_disc.py': '/root/agri/bot/handlers/ssd_disc.py'
};

conn.on('ready', () => {
  console.log('SSH Connected');
  let results = {};
  let pending = Object.keys(files).length;
  
  Object.entries(files).forEach(([name, remotePath]) => {
    conn.exec(`cat "${remotePath}"`, (err, stream) => {
      if (err) {
        results[name] = { error: err.message };
        done();
        return;
      }
      let stdout = '';
      let stderr = '';
      stream.on('data', (data) => { stdout += data.toString(); });
      stream.stderr.on('data', (data) => { stderr += data.toString(); });
      stream.on('close', (code) => {
        if (code !== 0) {
          results[name] = { error: stderr || `Exit code ${code}` };
        } else {
          results[name] = { content: stdout };
        }
        done();
      });
    });
  });
  
  function done() {
    if (--pending === 0) {
      const outPath = '/home/node/.openclaw/workspace/audit_vps_files.json';
      fs.writeFileSync(outPath, JSON.stringify(results, null, 2));
      console.log('All files saved to', outPath);
      conn.end();
    }
  }
});

conn.connect({
  host: '5.223.81.16',
  username: 'root',
  privateKey: privateKey
});
