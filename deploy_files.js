const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

// Files to deploy: local_path -> remote_path  
const FILES = [
  { local: '/tmp/v2_finance.py',     remote: '/root/staging/bot_src/bot/handlers/finance.py' },
  { local: '/tmp/v2_reports.py',     remote: '/root/staging/bot_src/bot/handlers/reports.py' },
  { local: '/tmp/v2_payroll.py',     remote: '/root/staging/bot_src/bot/handlers/payroll.py' },
  { local: '/tmp/v2_salary_adv.py',  remote: '/root/staging/bot_src/bot/handlers/salary_adv.py' },
  { local: '/tmp/v2_admin.py',       remote: '/root/staging/bot_src/bot/handlers/admin.py' },
  { local: '/tmp/v2_broadcast.py',   remote: '/root/staging/bot_src/bot/handlers/broadcast.py' },
  { local: '/tmp/v2_attendance.py',  remote: '/root/staging/bot_src/bot/handlers/attendance.py' },
];

conn.on('ready', () => {
  let remaining = FILES.length;
  FILES.forEach(({ local, remote }) => {
    conn.sftp((err, sftp) => {
      if (err) { console.error(`SFTP error: ${err}`); remaining--; if (remaining === 0) conn.end(); return; }
      sftp.fastPut(local, remote, (err) => {
        if (err) {
          console.error(`Error uploading ${local} -> ${remote}: ${err.message}`);
        } else {
          console.log(`OK: ${local} -> ${remote}`);
        }
        remaining--;
        if (remaining === 0) conn.end();
      });
    });
  });
});

conn.on('error', (err) => {
  console.error('Connection error:', err.message);
  process.exit(1);
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000,
});
