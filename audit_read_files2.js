const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');
const BASE = '/root/psvibe-sales-bot/bot';

const files = {
  'api_client.py': BASE + '/api_client.py',
  'app.py': BASE + '/app.py',
  'booking.py': BASE + '/handlers/booking.py',
  'booking_flow.py': BASE + '/handlers/booking_flow.py',
  'stock.py': BASE + '/handlers/stock.py',
  'stock_in.py': BASE + '/handlers/stock_in.py',
  'referral.py': BASE + '/handlers/referral.py',
  'discount.py': BASE + '/handlers/discount.py',
  'waitlist.py': BASE + '/handlers/waitlist.py',
  'attendance.py': BASE + '/handlers/attendance.py',
  'broadcast.py': BASE + '/handlers/broadcast.py',
  'notify.py': BASE + '/handlers/notify.py',
  'games.py': BASE + '/handlers/games.py',
  'ssd_disc.py': BASE + '/handlers/ssd_disc.py'
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
      const outPath = '/home/node/.openclaw/workspace/audit_vps_files2.json';
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
