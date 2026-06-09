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
        
        // Check what functions are missing in step_admin_menu
        console.log('Checking current admin.py step_admin_menu function...');
        const stepFunction = await executeCommand('cd /root/psvibe-sales-bot && sed -n "81,120p" bot/handlers/admin.py');
        console.log('Step function (lines 81-120):', stepFunction.output);
        
        // Check if there are attendance functions imported
        console.log('Checking for cmd_setattend function...');
        const cmdSetattend = await executeCommand('cd /root/psvibe-sales-bot && grep -n "def cmd_setattend\\|async def cmd_setattend" bot/handlers/*.py bot/__init__.py || echo "NOT FOUND"');
        console.log('cmd_setattend function:', cmdSetattend.output);
        
        // Check for attendance-related handlers
        console.log('Checking for attendance handlers...');
        const attendHandlers = await executeCommand('cd /root/psvibe-sales-bot && grep -r "attendance\\|ATTEND" bot/handlers/ --include="*.py" | head -10');
        console.log('Attendance handlers:', attendHandlers.output);
        
        conn.end();
        
    } catch (error) {
        console.error('Error:', error);
        conn.end();
    }
}

main();