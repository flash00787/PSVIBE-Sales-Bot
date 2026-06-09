const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HANDLERS = [
  'admin_bookings.py', 'admin.py', 'attendance.py', 'booking_flow.py',
  'booking.py', 'broadcast.py', 'commands.py', 'console_mgmt.py',
  'console.py', 'discount.py', 'finance.py', 'games.py', 'ginst.py',
  'help.py', '__init__.py', 'main_menu.py', 'members.py', 'notify.py',
  'payroll.py', 'referral.py', 'reports.py', 'salary_adv.py',
  'sales.py', 'ssd_disc.py', 'stock_in.py', 'stock.py', 'waitlist.py'
];

const outDir = '/home/node/.openclaw/workspace/audit/handlers';
fs.mkdirSync(outDir, { recursive: true });

// Build one cat command per file, separated by markers
// Use shell-safe delimiter
let cmd = 'cd /root/psvibe-sale-bot/bot/handlers && { ';
const lines = HANDLERS.map((f, i) => {
  const marker = `__FILE_MARKER_${i}__`;
  return `echo "${marker}" && cat "${f}"`;
});
cmd += lines.join(' && echo "---" && ') + '; }';
console.log('Cmd length:', cmd.length);

const conn = new Client();
conn.on('ready', () => {
  console.log('Connected. Fetching all files in one channel...');
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('exec err:', err); conn.end(); return; }
    let data = '';
    stream.on('data', chunk => { data += chunk.toString(); });
    stream.stderr.on('data', chunk => console.error('stderr:', chunk.toString()));
    stream.on('close', (code) => {
      console.log(`Stream closed with code ${code}, got ${data.length} bytes`);
      
      // Parse: split by __FILE_MARKER_N__
      const markerPat = /__FILE_MARKER_(\d+)__/g;
      const segments = [];
      let lastIdx = 0;
      let match;
      while ((match = markerPat.exec(data)) !== null) {
        segments.push({ idx: parseInt(match[1]), start: match.index + match[0].length });
        if (segments.length > 1) {
          segments[segments.length - 2].content = data.substring(segments[segments.length - 2].start, match.index).trim();
        }
      }
      if (segments.length > 0) {
        segments[segments.length - 1].content = data.substring(segments[segments.length - 1].start).trim();
      }
      
      let count = 0;
      segments.forEach(seg => {
        const fname = HANDLERS[seg.idx];
        if (fname && seg.content !== undefined && seg.content.length > 0) {
          // Remove trailing "---" marker
          let content = seg.content;
          if (content.endsWith('---')) content = content.slice(0, -3).trim();
          fs.writeFileSync(path.join(outDir, fname), content);
          console.log(`Wrote: ${fname} (${content.length} bytes)`);
          count++;
        }
      });
      console.log(`Total files written: ${count}`);      
      conn.end();
      process.exit(0);
    });
  });
}).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 20000
});
conn.on('error', err => { console.error('SSH Error:', err); process.exit(1); });
