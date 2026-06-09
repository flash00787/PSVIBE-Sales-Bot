const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected');

  const commands = [
    `cd /root/psvibe-sales-bot
FAIL_COUNT=0
for f in $(find . -name "*.py" -type f | grep -v __pycache__ | sort); do
  result=$(python3 -m py_compile "$f" 2>&1)
  if [ $? -ne 0 ]; then
    echo "FAIL: $f"
    echo "  $result"
    FAIL_COUNT=$((FAIL_COUNT+1))
  else
    echo "OK: $f"
  fi
done
echo "COMPILE_FAILURES=$FAIL_COUNT"
`,
    `cd /root/psvibe-sales-bot && grep -n "^import\|^from" main.py 2>/dev/null || echo "NO_MAIN_PY"`,
    `ls /root/psvibe-sales-bot/bot/handlers/ 2>/dev/null | grep "\\.py$" || echo "NO_HANDLERS"`,
    `python3 -c "compile(open('/root/psvibe-sales-bot/bot/__init__.py').read(), 'init.py', 'exec')" 2>&1 && echo "INIT_OK" || echo "INIT_FAIL"`,
    `cd /root/psvibe-sales-bot && find . -name "*.py" -type f | grep -v __pycache__ | xargs wc -l 2>/dev/null | tail -5`
  ];

  let idx = 0;
  const labels = [
    '\n=== 1. COMPILE ALL .py FILES ===',
    '\n=== 2. IMPORTS IN main.py ===',
    '\n=== 3. HANDLER FILES ===',
    '\n=== 4. __init__.py SYNTAX CHECK ===',
    '\n=== 5. LINE COUNT ==='
  ];

  function runNext() {
    if (idx >= commands.length) {
      conn.end();
      return;
    }
    console.log(labels[idx]);
    conn.exec(commands[idx], (err, stream) => {
      if (err) { console.error('exec error:', err); conn.end(); return; }
      let output = '';
      stream.on('data', (data) => { output += data.toString(); });
      stream.stderr.on('data', (data) => { output += data.toString(); });
      stream.on('close', () => {
        console.log(output.trim());
        idx++;
        runNext();
      });
    });
  }

  runNext();
});

conn.on('error', (err) => {
  console.error('SSH connection error:', err);
  process.exit(1);
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
