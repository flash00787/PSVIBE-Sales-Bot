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
        // Read private key
        const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
        
        await new Promise((resolve, reject) => {
            conn.on('ready', resolve).on('error', reject).connect({
                host: '5.223.81.16',
                username: 'root',
                privateKey: privateKey
            });
        });
        
        console.log('Connected to VPS');
        
        // Start fix protocol
        console.log('Starting fix protocol...');
        const fixStart = await executeCommand('cd /root/psvibe-sales-bot && python3 /root/coordination/fix_protocol.py --start bot/handlers/admin.py');
        console.log('Fix protocol start:', fixStart.output);
        
        // Read admin.py file
        console.log('Reading admin.py...');
        const adminFile = await executeCommand('cd /root/psvibe-sales-bot && cat bot/handlers/admin.py');
        console.log('Admin file length:', adminFile.output.length);
        
        // Save admin.py content locally for analysis
        fs.writeFileSync('/home/node/.openclaw/workspace/temp/admin_original.py', adminFile.output);
        
        // Search for stock-related functions
        console.log('Searching for stock-related functions...');
        const stockSearch = await executeCommand('cd /root/psvibe-sales-bot && grep -r "stock\\|inventory\\|STOCK\\|cmd_stock" bot/ --include="*.py" || true');
        console.log('Stock search results:', stockSearch.output);
        
        // Check constants.py for BTN_STOCK_UPDATE
        console.log('Checking constants.py...');
        const constants = await executeCommand('cd /root/psvibe-sales-bot && grep -n "BTN_STOCK\\|BTN_ADMIN_ATTEND" bot/constants.py || true');
        console.log('Constants search:', constants.output);
        
        // Check __init__.py for states
        console.log('Checking __init__.py for states...');
        const initFile = await executeCommand('cd /root/psvibe-sales-bot && grep -n "STOCK\\|ATTEND" bot/__init__.py || true');
        console.log('Init states:', initFile.output);
        
        // Check gsheet.py for sheet references
        console.log('Checking gsheet.py...');
        const gsheet = await executeCommand('cd /root/psvibe-sales-bot && cat bot/gsheet.py | head -50');
        console.log('GSheet file start:', gsheet.output);
        
        conn.end();
        
    } catch (error) {
        console.error('Error:', error);
        conn.end();
    }
}

main();