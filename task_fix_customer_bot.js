const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();

const keyPath = '/home/node/.openclaw/workspace/.ssh/id_rsa';

conn.on('ready', () => {
  console.log('SSH connected.\n');

  const steps = [
    {
      label: 'Step 1 — Read current systemd service',
      cmd: 'cat /etc/systemd/system/psvibe_customer_bot.service'
    },
    {
      label: 'Step 2 — Update ExecStart',
      cmd: `sed -i 's|customer_bot_original.py|customer_bot/main.py|g' /etc/systemd/system/psvibe_customer_bot.service && cat /etc/systemd/system/psvibe_customer_bot.service`
    },
    {
      label: 'Step 3 — Reload systemd + verify ExecStart',
      cmd: `systemctl daemon-reload && systemctl cat psvibe_customer_bot.service 2>/dev/null | grep ExecStart`
    },
    {
      label: 'Step 4 — Start customer bot service + status',
      cmd: `systemctl start psvibe_customer_bot.service 2>&1; sleep 2; systemctl status psvibe_customer_bot.service --no-pager -l 2>&1 | head -30`
    },
    {
      label: 'Step 5 — Clean up stale files',
      cmd: `rm -f /root/psvibe_sales_bot/__pycache__/customer_bot_original.cpython-312.pyc /root/psvibe_sales_bot/__pycache__/customer_bot_original.cpython-311.pyc /root/psvibe_sales_bot/trash/customer_bot_original.py && echo 'Cleanup done'`
    },
    {
      label: 'Step 6 — Final verification',
      cmd: `echo '=== Running psvibe processes ==='; ps aux | grep -E 'python.*(psvibe|customer_bot)' | grep -v grep; echo ''; echo '=== Enabled status ==='; systemctl is-enabled psvibe_customer_bot.service 2>/dev/null; systemctl is-enabled psvibe_sales_bot.service 2>/dev/null`
    }
  ];

  let idx = 0;

  function runNext() {
    if (idx >= steps.length) {
      conn.end();
      return;
    }
    const step = steps[idx++];
    console.log(`\n${'='.repeat(60)}`);
    console.log(`${step.label}`);
    console.log(`${'='.repeat(60)}`);
    conn.exec(step.cmd, (err, stream) => {
      if (err) {
        console.error(`EXEC ERROR: ${err.message}`);
        runNext();
        return;
      }
      let out = '';
      let errOut = '';
      stream.on('data', (d) => { out += d.toString(); });
      stream.stderr.on('data', (d) => { errOut += d.toString(); });
      stream.on('close', (code) => {
        if (out) console.log(out);
        if (errOut) console.error('STDERR:', errOut);
        console.log(`exit code: ${code}`);
        runNext();
      });
    });
  }

  runNext();
});

conn.on('error', (err) => {
  console.error('SSH error:', err.message);
  process.exit(1);
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync(keyPath),
  readyTimeout: 15000
});
