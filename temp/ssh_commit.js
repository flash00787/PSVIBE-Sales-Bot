const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

function execCommand(command) {
    return new Promise((resolve, reject) => {
        conn.exec(command, (err, stream) => {
            if (err) return reject(err);
            
            let stdout = '';
            let stderr = '';
            
            stream.on('close', (code, signal) => {
                resolve({ stdout, stderr, code });
            }).on('data', (data) => {
                stdout += data;
            }).stderr.on('data', (data) => {
                stderr += data;
            });
        });
    });
}

async function main() {
    try {
        console.log('=== Committing existing changes ===');
        
        // Check status
        const statusResult = await execCommand('cd /root/psvibe-sales-bot && git status --porcelain');
        console.log('Git status:', statusResult.stdout);
        
        // Add all changes
        const addResult = await execCommand('cd /root/psvibe-sales-bot && git add -A');
        console.log('Git add result:', addResult.stdout, addResult.stderr);
        
        // Commit
        const commitResult = await execCommand('cd /root/psvibe-sales-bot && git commit -m "Pre-fix commit: backup files and init changes"');
        console.log('Git commit result:', commitResult.stdout, commitResult.stderr);
        
        // Now start fix protocol
        console.log('=== Starting Fix Protocol ===');
        const startResult = await execCommand('cd /root/psvibe-sales-bot && python3 /root/coordination/fix_protocol.py --start bot/handlers/members.py');
        console.log('Fix Protocol Start:', startResult.stdout, startResult.stderr);

        conn.end();
        
    } catch (error) {
        console.error('SSH Error:', error);
        conn.end();
    }
}

conn.on('ready', () => {
    console.log('SSH Connected');
    main();
}).connect({
    host: '5.223.81.16',
    username: 'root',
    privateKey: privateKey
});