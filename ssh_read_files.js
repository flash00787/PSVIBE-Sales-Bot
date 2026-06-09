const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

const filesToRead = [
  '/root/psvibe-sales-bot/customer_bot/api.py',
  '/root/psvibe-sales-bot/customer_bot/data/prompts.py',
  '/root/psvibe-sales-bot/customer_bot/booking_handlers.py'
];

const results = {};

conn.on('ready', () => {
  console.log('SSH connected!');
  let pending = filesToRead.length;
  
  filesToRead.forEach((filePath) => {
    conn.exec(`cat "${filePath}"`, (err, stream) => {
      if (err) {
        results[filePath] = `ERROR: ${err.message}`;
        if (--pending === 0) finish();
        return;
      }
      let data = '';
      stream.on('data', (chunk) => { data += chunk.toString(); });
      stream.on('close', (code) => {
        results[filePath] = { code, data };
        if (--pending === 0) finish();
      });
      stream.stderr.on('data', (chunk) => {
        results[filePath + '.stderr'] = chunk.toString();
      });
    });
  });
  
  function finish() {
    fs.writeFileSync('/home/node/.openclaw/workspace/temp/ssh_read_results.json', JSON.stringify(results, null, 2));
    console.log('DONE - results written');
    conn.end();
  }
});

conn.on('error', (err) => {
  console.error('Connection error:', err);
  process.exit(1);
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
