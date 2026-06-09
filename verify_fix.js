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
        
        console.log('Connected to VPS - Final Verification');
        
        // Check fix protocol status
        const fixStatus = await executeCommand('cd /root/psvibe-sales-bot && python3 /root/coordination/fix_protocol.py --status');
        console.log('Fix protocol status:', fixStatus.output);
        
        // Check if the function was properly added
        const funcCheck = await executeCommand('cd /root/psvibe-sales-bot && grep -A 5 "def cmd_admin_sal_adv" bot/handlers/admin.py');
        console.log('\\nFunction verification:', funcCheck.output);
        
        // Final compilation verification
        const compileCheck = await executeCommand('cd /root/psvibe-sales-bot && python3 -m py_compile bot/handlers/admin.py');
        console.log('\\nFinal compile check:', compileCheck.error || 'SUCCESS');
        
        conn.end();
        
    } catch (error) {
        console.error('Error:', error);
        conn.end();
    }
}

main();