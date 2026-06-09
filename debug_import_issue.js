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
        
        // Let's test the bot directly to see what error we get
        console.log('Testing the current bot behavior...');
        
        // Check the import section of admin.py more carefully
        console.log('Checking imports in admin.py...');
        const imports = await executeCommand('cd /root/psvibe-sales-bot && head -15 bot/handlers/admin.py');
        console.log('Admin.py imports:', imports.output);
        
        // Actually, let me test if there's a syntax/compile error
        console.log('Compiling admin.py...');
        const compile = await executeCommand('cd /root/psvibe-sales-bot && python3 -m py_compile bot/handlers/admin.py');
        console.log('Compile result:', compile.output, compile.error);
        
        // Check git status to see what changed
        console.log('Git status check...');
        const gitStatus = await executeCommand('cd /root/psvibe-sales-bot && git status --porcelain');
        console.log('Git status:', gitStatus.output);
        
        conn.end();
        
    } catch (error) {
        console.error('Error:', error);
        conn.end();
    }
}

main();