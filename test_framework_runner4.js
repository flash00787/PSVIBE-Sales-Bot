const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const commands = [];

function cmd(c) { commands.push(c); }

// Syntax check all test files
cmd('echo "=== SYNTAX CHECKS ==="');
cmd('cd /root/psvibe-sales-bot && python3 -m py_compile tests/conftest.py 2>&1 && echo "conftest.py: OK" || echo "conftest.py: FAIL"');
cmd('cd /root/psvibe-sales-bot && python3 -m py_compile tests/test_main_menu.py 2>&1 && echo "test_main_menu.py: OK" || echo "test_main_menu.py: FAIL"');
cmd('cd /root/psvibe-sales-bot && python3 -m py_compile tests/test_members.py 2>&1 && echo "test_members.py: OK" || echo "test_members.py: FAIL"');
cmd('cd /root/psvibe-sales-bot && python3 -m py_compile tests/test_sales.py 2>&1 && echo "test_sales.py: OK" || echo "test_sales.py: FAIL"');
cmd('cd /root/psvibe-sales-bot && python3 -m py_compile tests/test_booking.py 2>&1 && echo "test_booking.py: OK" || echo "test_booking.py: FAIL"');
cmd('cd /root/psvibe-sales-bot && python3 -m py_compile tests/test_reports.py 2>&1 && echo "test_reports.py: OK" || echo "test_reports.py: FAIL"');
cmd('cd /root/psvibe-sales-bot && python3 -m py_compile tests/test_finance.py 2>&1 && echo "test_finance.py: OK" || echo "test_finance.py: FAIL"');
cmd('cd /root/psvibe-sales-bot && python3 -m py_compile tests/test_stock.py 2>&1 && echo "test_stock.py: OK" || echo "test_stock.py: FAIL"');

// Run pytest (all tests)
cmd('echo "=== RUNNING PYTEST ==="');
cmd('cd /root/psvibe-sales-bot && python3 -m pytest tests/ -v --tb=short --no-header 2>&1; echo "EXIT_CODE=$?"');

console.log("Phase 4 commands loaded. Connecting...");

conn.on('ready', () => {
    let cmdIndex = 0;
    let outputBuffer = '';

    function runNext() {
        if (cmdIndex >= commands.length) { conn.end(); return; }
        const c = commands[cmdIndex];
        cmdIndex++;
        conn.exec(c, (err, stream) => {
            if (err) { outputBuffer += 'ERR: ' + err + '\n'; runNext(); return; }
            stream.on('data', (d) => { outputBuffer += d.toString(); });
            stream.stderr.on('data', (d) => { outputBuffer += d.toString(); });
            stream.on('close', () => runNext());
        });
    }

    conn.on('close', () => {
        fs.writeFileSync('/home/node/.openclaw/workspace/test_framework_output4.txt', outputBuffer);
        console.log('\nPhase 4 complete.');
    });

    runNext();
});

conn.connect({
    host: '5.223.81.16',
    port: 22,
    username: 'root',
    privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
