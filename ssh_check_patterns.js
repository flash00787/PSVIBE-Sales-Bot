const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
let results = [];
let pending = 0;

function runCmd(cmd) {
  return new Promise((resolve) => {
    pending++;
    conn.exec(cmd, (err, stream) => {
      if (err) { results.push(`ERR: ${err.message}`); pending--; resolve(); return; }
      let out = '';
      stream.on('data', (d) => out += d.toString());
      stream.on('close', () => { results.push(out); pending--; resolve(); });
    });
  });
}

conn.on('ready', async () => {
  console.log('Connected');

  // Check exact lines with grep
  await runCmd('grep -n "games = (data" /root/psvibe-sales-bot/customer_bot/api.py');
  await runCmd('grep -n "promos = (data" /root/psvibe-sales-bot/customer_bot/api.py');
  await runCmd('grep -n "build_live_game_library_fn" /root/psvibe-sales-bot/customer_bot/data/prompts.py');
  await runCmd('grep -n "bookings?date=" /root/psvibe-sales-bot/customer_bot/booking_handlers.py');
  await runCmd('grep -n "bookings?telegramChatId" /root/psvibe-sales-bot/customer_bot/booking_handlers.py');
  // Also check for the multiline version
  await runCmd('grep -n "bookings/search" /root/psvibe-sales-bot/customer_bot/booking_handlers.py');

  while (pending > 0) { await new Promise(r => setTimeout(r, 100)); }
  console.log('---RESULTS---');
  results.forEach(r => console.log(r));
  conn.end();
});

conn.on('error', (err) => { console.error('Error:', err); process.exit(1); });
conn.connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
