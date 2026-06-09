const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

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
        // Read members.py
        console.log('=== Reading members.py ===');
        const result1 = await execCommand('cat /root/psvibe-sales-bot/bot/handlers/members.py');
        if (result1.code === 0) {
            console.log('members.py length:', result1.stdout.length);
            fs.writeFileSync('/home/node/.openclaw/workspace/temp/members.py', result1.stdout);
        } else {
            console.log('Error reading members.py:', result1.stderr);
        }

        // Read constants.py
        console.log('=== Reading constants.py ===');
        const result2 = await execCommand('cat /root/psvibe-sales-bot/bot/constants.py');
        if (result2.code === 0) {
            console.log('constants.py length:', result2.stdout.length);
            fs.writeFileSync('/home/node/.openclaw/workspace/temp/constants.py', result2.stdout);
        } else {
            console.log('Error reading constants.py:', result2.stderr);
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