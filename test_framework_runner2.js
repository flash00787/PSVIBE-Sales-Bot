const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const commands = [];

function cmd(c) { commands.push(c); }

// Read key handler files to understand patterns
cmd('head -80 /root/psvibe-sales-bot/bot/handlers/main_menu.py');
cmd('head -80 /root/psvibe-sales-bot/bot/handlers/sales.py');
cmd('head -80 /root/psvibe-sales-bot/bot/handlers/members.py');
cmd('head -80 /root/psvibe-sales-bot/bot/handlers/booking.py');
cmd('head -80 /root/psvibe-sales-bot/bot/handlers/reports.py');
cmd('head -80 /root/psvibe-sales-bot/bot/handlers/finance.py');
cmd('head -80 /root/psvibe-sales-bot/bot/handlers/stock.py');
cmd('head -80 /root/psvibe-sales-bot/bot/handlers/discount.py');

conn.on('ready', () => {
    let cmdIndex = 0;
    let outputBuffer = '';

    function runNext() {
        if (cmdIndex >= commands.length) { conn.end(); return; }
        const c = commands[cmdIndex];
        cmdIndex++;
        console.log(`### CMD ${cmdIndex}/${commands.length}: ${c.substring(0,70)}...`);
        conn.exec(c, (err, stream) => {
            if (err) { outputBuffer += `ERR: ${err}\n`; runNext(); return; }
            stream.on('data', (d) => { outputBuffer += d.toString(); });
            stream.stderr.on('data', (d) => { outputBuffer += d.toString(); });
            stream.on('close', () => runNext());
        });
    }

    conn.on('close', () => {
        fs.writeFileSync('/home/node/.openclaw/workspace/test_framework_output2.txt', outputBuffer);
        console.log('\nPhase 2 complete.');
    });

    runNext();
});

conn.connect({
    host: '5.223.81.16',
    port: 22,
    username: 'root',
    privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
