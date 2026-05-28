const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

const commands = [
  'echo "=== BOT 2 DIRECTORY STRUCTURE ===" && find /root/Personal-Wallet-Tele-Bot-2 -maxdepth 3 -not -path "*/.*" -not -path "*/venv/*" -not -path "*/node_modules/*" -not -path "*/artifacts/*" | sort'
];

const fullCommand = commands.join('\n\necho ""\n\n');

conn.on('ready', () => {
  conn.exec(fullCommand, (err, stream) => {
    if (err) {
      console.error('Exec error:', err);
      conn.end();
      process.exit(1);
    }
    let stdout = '';
    let stderr = '';
    stream.on('close', (code, signal) => {
      console.log(`Exit code: ${code}`);
      console.log('--- STDOUT ---');
      console.log(stdout);
      console.log('--- STDERR ---');
      console.log(stderr);
      conn.end();
    }).on('data', (data) => {
      stdout += data.toString();
    }).stderr.on('data', (data) => {
      stderr += data.toString();
    });
  });
}).on('error', (err) => {
  console.error('Connection error:', err);
  process.exit(1);
}).connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
