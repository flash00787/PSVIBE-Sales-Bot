const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Check the auto-commit for pending bookings fix
  'cd /root/psvibe-sales-bot && git show 3c094b5 --stat',
  'cd /root/psvibe-sales-bot && git log --all --oneline --grep="pending" -5',
  'cd /root/psvibe-sales-bot && git log --all --oneline --grep="booking" -5',
  // Check if there are pending bookings handler files
  'cd /root/psvibe-sales-bot && grep -n "Pending\|pending" bot/handlers/admin_bookings.py | head -20',
  // Check service restart time vs latest commit
  'cd /root/psvibe-sales-bot && git log -1 --format="%H %ai"',
  // Check for any uncommitted changes in common areas
  'cd /root/psvibe-sales-bot && git stash list',
  'cd /root/psvibe-sales-bot && journalctl -u psvibe-sale-bot --since "1 hour ago" --no-pager 2>&1 | grep -iE "pending|error|warn" | tail -20'
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
