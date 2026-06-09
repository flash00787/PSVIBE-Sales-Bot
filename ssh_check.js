const { Client } = require('ssh2');
const fs = require('fs');

const commands = [
  'cd /root/psvibe-sales-bot && python3 -m py_compile customer_bot/booking.py 2>&1; echo "EXIT:$?"',
  'cd /root/psvibe-sales-bot && python3 -c "from customer_bot.booking import cmd_mybookings, _format_booking_line, cmd_cancel_booking; print(\'IMPORT OK\')" 2>&1; echo "EXIT:$?"',
  'journalctl -u psvibe_customer_bot --no-pager -n 30 2>&1 | tail -30',
  'journalctl -u psvibe_customer_bot --no-pager --since "2 hours ago" 2>&1 | grep -i -E "booking|error|traceback|task was destroyed|mybooking" | tail -20',
];

const conn = new Client();

conn.on('ready', () => {
  let pending = commands.length;
  const results = {};
  
  commands.forEach((cmd, idx) => {
    conn.exec(cmd, (err, stream) => {
      if (err) { results[idx] = `ERROR: ${err.message}`; if (--pending === 0) done(); return; }
      let data = '';
      stream.on('data', (chunk) => { data += chunk; });
      stream.stderr.on('data', (chunk) => { data += chunk; });
      stream.on('close', () => { results[idx] = data; if (--pending === 0) done(); });
    });
  });
  
  function done() {
    commands.forEach((cmd, i) => {
      console.log(`=== CMD ${i}: ${cmd} ===`);
      console.log(results[i]);
      console.log(`=== END ${i} ===\n`);
    });
    conn.end();
  }
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err.message);
  process.exit(1);
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000,
});
