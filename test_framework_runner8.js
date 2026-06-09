const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const commands = [];

function cmd(c) { commands.push(c); }

// Read ALL files that bot/handlers/__init__.py imports transitively
// to find every constant/function imported from "bot"
cmd('echo "=== HANDLERS INIT ==="');
cmd('cat /root/psvibe-sales-bot/bot/handlers/__init__.py');
cmd('echo "=== HELP.PY ==="');
cmd('cat /root/psvibe-sales-bot/bot/handlers/help.py');
cmd('echo "=== GINST.PY top imports ==="');
cmd('head -30 /root/psvibe-sales-bot/bot/handlers/ginst.py');
cmd('echo "=== COMMANDS.PY ==="');
cmd('head -30 /root/psvibe-sales-bot/bot/handlers/commands.py');
cmd('echo "=== CONSOLE_MGMT.PY top ==="');
cmd('head -30 /root/psvibe-sales-bot/bot/handlers/console_mgmt.py');
cmd('echo "=== NOTIFY.PY ==="');
cmd('head -30 /root/psvibe-sales-bot/bot/handlers/notify.py');

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
        fs.writeFileSync('/home/node/.openclaw/workspace/test_framework_output8.txt', outputBuffer);
        console.log('\nInspection complete.');
    });

    runNext();
});

conn.connect({
    host: '5.223.81.16',
    port: 22,
    username: 'root',
    privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
