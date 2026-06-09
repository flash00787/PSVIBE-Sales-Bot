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
        // Look for fetch_payment_methods definition
        console.log('=== Searching for fetch_payment_methods ===');
        const result1 = await execCommand('grep -rn "def fetch_payment_methods" /root/psvibe-sales-bot/bot/');
        console.log('Search result:', result1.stdout, result1.stderr);

        // Check __init__.py specifically
        const result2 = await execCommand('grep -A 10 -B 5 "fetch_payment_methods" /root/psvibe-sales-bot/bot/__init__.py');
        if (result2.stdout) {
            console.log('__init__.py content:', result2.stdout);
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