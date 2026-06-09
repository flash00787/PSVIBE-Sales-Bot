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
        // Commit any remaining changes
        console.log('=== Final commit ===');
        const addResult2 = await execCommand('cd /root/psvibe-sales-bot && git add -A');
        console.log('Git add result:', addResult2.stdout, addResult2.stderr);
        
        const commitResult2 = await execCommand('cd /root/psvibe-sales-bot && git commit -m "Post pre-commit hooks cleanup"');
        console.log('Git commit result:', commitResult2.stdout, commitResult2.stderr);
        
        // Now start fix protocol
        console.log('=== Starting Fix Protocol ===');
        const startResult = await execCommand('cd /root/psvibe-sales-bot && python3 /root/coordination/fix_protocol.py --start bot/handlers/members.py');
        console.log('Fix Protocol Start:', startResult.stdout, startResult.stderr);

        if (startResult.code !== 0) {
            console.error('Fix protocol failed');
        } else {
            console.log('✅ Fix protocol started successfully');
        }

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