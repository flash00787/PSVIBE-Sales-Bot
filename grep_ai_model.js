const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected - checking AI model configurations');
  
  const commands = [
    'grep -in "model" /root/Personal-Wallet-Tele-Bot-2/bot/main.py | head -20',
    'grep -in "gemini\\|openai\\|ai_" /root/Personal-Wallet-Tele-Bot-2/bot/main.py | head -20',
    'cat /root/Personal-Wallet-Tele-Bot-2/bot/.env 2>&1 | grep -i "model\\|api\\|gemini\\|openai"'
  ];

  let idx = 0;
  
  function runNext() {
    if (idx >= commands.length) {
      conn.end();
      return;
    }
    const cmd = commands[idx++];
    console.log(`\n>>> COMMAND: ${cmd}`);
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
