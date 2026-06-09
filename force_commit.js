const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

async function executeCommand(command) {
    return new Promise((resolve, reject) => {
        conn.exec(command, (err, stream) => {
            if (err) return reject(err);
            
            let output = '';
            let error = '';
            
            stream.on('close', (code) => {
                resolve({ output, error, code });
            }).on('data', (data) => {
                output += data.toString();
            }).stderr.on('data', (data) => {
                error += data.toString();
            });
        });
    });
}

async function main() {
    try {
        const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
        
        await new Promise((resolve, reject) => {
            conn.on('ready', resolve).on('error', reject).connect({
                host: '5.223.81.16',
                username: 'root',
                privateKey: privateKey
            });
        });
        
        console.log('Connected to VPS');
        
        // Force commit
        const commit = await executeCommand('cd /root/psvibe-sales-bot && git add -A && git commit -m "Pre-inventory-fix commit - backing up WIP changes"');
        console.log('Commit result:', commit.output, commit.error);
        
        // Now try fix protocol again
        const fixStart = await executeCommand('cd /root/psvibe-sales-bot && python3 /root/coordination/fix_protocol.py --start bot/handlers/admin.py');
        console.log('Fix protocol start:', fixStart.output);
        
        // The issue might be that I misunderstood the problem. Let me check what the user actually means by "dead buttons"
        // Looking at the task again: "When user presses "Stock Update" or "Attendance", the function falls through all if checks"
        // This suggests the button text doesn't match the constants. Let me verify:
        
        console.log('Checking BTN_STOCK_UPDATE and BTN_ADMIN_ATTEND values...');
        const btnValues = await executeCommand('cd /root/psvibe-sales-bot && grep -n "BTN_STOCK_UPDATE\\|BTN_ADMIN_ATTEND" bot/constants.py');
        console.log('Button values:', btnValues.output);
        
        conn.end();
        
    } catch (error) {
        console.error('Error:', error);
        conn.end();
    }
}

main();