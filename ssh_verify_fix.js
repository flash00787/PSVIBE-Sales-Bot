const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected - verifying fixes');
  
  const commands = [
    // Verify the import line
    "sed -n '27,29p' /root/Personal-Wallet-Tele-Bot-2/bot/main.py",
    // Verify the error_handler
    "sed -n '2605,2629p' /root/Personal-Wallet-Tele-Bot-2/bot/main.py",
    // Verify the self-healing loop
    "sed -n '2893,2913p' /root/Personal-Wallet-Tele-Bot-2/bot/main.py",
    // Syntax check
    '/root/Personal-Wallet-Tele-Bot-2/bot/venv/bin/python3 -m py_compile /root/Personal-Wallet-Tele-Bot-2/bot/main.py 2>&1 && echo "SYNTAX OK"',
  ];

  let idx = 0;
  
  function runNext() {
    if (idx >= commands.length) {
      conn.end();
      return;
    }
    const cmd = commands[idx++];
    console.log(`\n>>> CMD ${idx}:`);
    conn.exec(cmd, { pty: false }, (err, stream) => {
      if (err) {
        console.log('EXEC ERROR:', err);
        runNext();
        return;
      }
      let output = '';
      stream.on('data', (data) => { output += data.toString(); });
      stream.stderr.on('data', (data) => { output += data.toString(); });
      stream.on('close', (code) => {
        console.log(output.trim() || '(no output)');
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
