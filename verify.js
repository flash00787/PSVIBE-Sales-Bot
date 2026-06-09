const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
const commands = [];

function cmd(c) { commands.push(c); }

cmd('echo "=== FINAL VERIFICATION ==="');
cmd('echo "--- Directory Structure ---"');
cmd('find /root/psvibe-sales-bot/tests -type f | sort');
cmd('echo "--- File Sizes ---"');
cmd('wc -l /root/psvibe-sales-bot/tests/*.py /root/psvibe-sales-bot/pytest.ini /root/coordination/test_runner.py /root/coordination/findings/test_framework.json');
cmd('echo "--- Findings JSON ---"');
cmd('cat /root/coordination/findings/test_framework.json');
cmd('echo "--- Test Runner ---"');
cmd('python3 /root/coordination/test_runner.py');
cmd('echo "--- All Syntax Good ---"');
cmd('cd /root/psvibe-sales-bot && for f in tests/*.py; do python3 -m py_compile "$f" 2>&1 && echo "$f: OK"; done');

conn.on('ready', () => {
    let idx = 0, buf = '';
    function next() {
        if (idx >= commands.length) { conn.end(); return; }
        conn.exec(commands[idx], (e, s) => {
            if (e) { buf += 'E:' + e; next(); return; }
            s.on('data', d => buf += d.toString());
            s.stderr.on('data', d => buf += d.toString());
            s.on('close', () => { idx++; next(); });
        });
    }
    next();
    conn.on('close', () => {
        fs.writeFileSync('/home/node/.openclaw/workspace/verify_final.txt', buf);
        console.log('Final verification complete.');
    });
});

conn.connect({
    host: '5.223.81.16', port: 22, username: 'root',
    privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
