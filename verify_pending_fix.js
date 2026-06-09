const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  'cd /root/psvibe-sales-bot && git diff HEAD~1 --stat',
  'cd /root/psvibe-sales-bot && git log --oneline -3',
  'cd /root/psvibe-sales-bot && git diff HEAD~1',
  'systemctl status psvibe-sale-bot | head -5',
  'journalctl -u psvibe-sale-bot -n 20 --no-pager 2>&1 | grep -i error',
  'cd /root/psvibe-sales-bot && git status',
  'cd /root/psvibe-sales-bot && git diff'
];

let results = {};
let cmdIdx = 0;

conn.on('ready', () => {
  runNext();
});

function runNext() {
  if (cmdIdx >= commands.length) {
    conn.end();
    console.log(JSON.stringify(results));
    return;
  }
  const cmd = commands[cmdIdx];
  const label = `cmd${cmdIdx}`;
  conn.exec(cmd, (err, stream) => {
    if (err) {
      results[label] = { cmd, stdout: '', stderr: `ERROR: ${err.message}` };
      cmdIdx++;
      runNext();
      return;
    }
    let stdout = '', stderr = '';
    stream.on('data', d => stdout += d.toString());
    stream.stderr.on('data', d => stderr += d.toString());
    stream.on('close', (code) => {
      results[label] = { cmd, stdout, stderr, exitCode: code };
      cmdIdx++;
      runNext();
    });
  });
}

conn.connect({
  host: '5.223.81.16',
  username: 'root',
  privateKey: key,
  readyTimeout: 10000
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err.message);
  process.exit(1);
});
