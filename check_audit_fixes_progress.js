const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH Connected — checking audit fixes progress on VPS');

  const commands = [
    {
      name: 'Check if Staging matches Production',
      cmd: 'diff -rq /root/Sales-Tele-Bot_staging /root/Sales-Tele-Bot || echo "Staging and Production differ"'
    },
    {
      name: 'Check Cache Sweeper and Cache Lock in Production customer_bot.py',
      cmd: 'grep -n -E "_CACHE_LOCK|_async_cache_sweeper" /root/Sales-Tele-Bot/customer_bot.py || echo "No cache lock/sweeper found in production"'
    },
    {
      name: 'Check API Retry Logic in Production customer_bot.py',
      cmd: 'grep -n -A 20 "def _api_get" /root/Sales-Tele-Bot/customer_bot.py'
    },
    {
      name: 'Check Bare Exception Logging in Production customer_bot.py',
      cmd: 'grep -n -C 3 "wl_claim" /root/Sales-Tele-Bot/customer_bot.py || grep -n -A 5 "except Exception" /root/Sales-Tele-Bot/customer_bot.py | head -n 30'
    },
    {
      name: 'Check if Staff Whitelist is still hardcoded in Production',
      cmd: 'grep -n -E "_ALLOWED_STAFF_IDS" /root/Sales-Tele-Bot/bot/app.py /root/Sales-Tele-Bot/bot/handlers.py || echo "Not found"'
    },
    {
      name: 'Check Stock PIN definition in Production',
      cmd: 'grep -n -E "STOCK_PIN|STOCK_ACCESS_PIN" /root/Sales-Tele-Bot/__init__.py /root/Sales-Tele-Bot/bot/handlers.py || echo "Not found"'
    },
    {
      name: 'Check if .env contains hardcoded credentials',
      cmd: 'cat /root/Sales-Tele-Bot/.env | grep -E "BOT_TOKEN|API_KEY|PIN" | sed "s/=.*/=REDACTED/" || echo "No .env or no credentials found"'
    }
  ];

  let idx = 0;

  function runNext() {
    if (idx >= commands.length) {
      conn.end();
      return;
    }
    const item = commands[idx++];
    console.log(`\n==================================================`);
    console.log(`🔍 CHECK: ${item.name}`);
    console.log(`==================================================`);
    conn.exec(item.cmd, { pty: false }, (err, stream) => {
      if (err) {
        console.log(`EXEC ERROR:`, err);
        runNext();
        return;
      }
      let output = '';
      stream.on('data', (data) => { output += data.toString(); });
      stream.stderr.on('data', (data) => { output += data.toString(); });
      stream.on('close', (code) => {
        console.log(output.trim() || '(No output)');
        runNext();
      });
    });
  }

  runNext();
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err);
  process.exit(1);
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
