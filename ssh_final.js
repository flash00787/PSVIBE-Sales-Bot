const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

function execCmd(cmd) {
  return new Promise((resolve, reject) => {
    let stdout = '', stderr = '';
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      stream.on('data', d => stdout += d.toString());
      stream.stderr.on('data', d => stderr += d.toString());
      stream.on('close', code => resolve({ code, stdout, stderr }));
    });
  });
}

conn.on('ready', async () => {
  try {
    // Wait for things to settle
    await new Promise(r => setTimeout(r, 10000));

    // Final status check
    let r = await execCmd('systemctl is-active psvibe-sale-bot.service 2>&1 && echo "---" && journalctl -u psvibe-sale-bot.service --no-pager -n 15 2>&1');
    console.log('=== FINAL STATUS ===');
    console.log(r.stdout);

    // Check no recent crash-loops
    r = await execCmd('journalctl -u psvibe-sale-bot.service --no-pager --since "2 min ago" | grep -c "Bot started"');
    console.log('Bot started count (last 2 min): ' + r.stdout.trim());

    r = await execCmd('journalctl -u psvibe-sale-bot.service --no-pager --since "2 min ago" | grep -c "Bot crashed\|ImportError\|NameError\|circular\|AttributeError"');
    console.log('Error count (last 2 min): ' + r.stdout.trim());

    // Show the final fix
    console.log('\n=== FIX APPLIED ===');
    r = await execCmd("cd /root/psvibe-sales-bot && sed -n '9,21p' bot/handlers/console_mgmt.py");
    console.log(r.stdout);

  } catch(e) {
    console.error('ERROR:', e.message);
  }
  conn.end();
});

conn.on('error', e => console.error('SSH error:', e.message));
conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
