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
        
        // Let's stash the changes and then properly test
        console.log('Stashing uncommitted changes...');
        const stash = await executeCommand('cd /root/psvibe-sales-bot && git add . && git commit -m "WIP: temp changes before inventory fix"');
        console.log('Stash result:', stash.output);
        
        // Now start fix protocol
        console.log('Starting fix protocol...');
        const fixStart = await executeCommand('cd /root/psvibe-sales-bot && python3 /root/coordination/fix_protocol.py --start bot/handlers/admin.py');
        console.log('Fix protocol start:', fixStart.output);
        
        // Let me also check if the issue is actually with the button layout itself
        console.log('Checking show_admin_menu function...');
        const adminMenu = await executeCommand('cd /root/psvibe-sales-bot && grep -A 20 "def show_admin_menu" bot/handlers/admin.py');
        console.log('Admin menu function:', adminMenu.output);
        
        conn.end();
        
    } catch (error) {
        console.error('Error:', error);
        conn.end();
    }
}

main();