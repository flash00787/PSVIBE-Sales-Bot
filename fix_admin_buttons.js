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
        
        // Force commit the changes first
        const commit = await executeCommand('cd /root/psvibe-sales-bot && git add . && git commit -m "Pre-fix commit: stashing changes" --allow-empty');
        console.log('Commit done');
        
        // Start fix protocol
        const fixStart = await executeCommand('cd /root/psvibe-sales-bot && python3 /root/coordination/fix_protocol.py --start bot/handlers/admin.py');
        console.log('Fix protocol started:', fixStart.output.split('\\n').slice(-5).join('\\n'));
        
        // Let me investigate if the issue is an import problem
        // First, check what functions are actually missing
        console.log('\\n=== CHECKING MISSING FUNCTIONS ===');
        const missingFunctions = await executeCommand(`cd /root/psvibe-sales-bot && grep -n "cmd_admin_sal_adv\\|cmd_admin_pnl\\|cmd_admin_cashflow\\|cmd_admin_liability\\|cmd_admin_bookings\\|cmd_staff_booking\\|cmd_confirmed_bookings\\|show_con_mgmt_menu\\|cmd_promo_reports" bot/handlers/admin.py`);
        console.log('Functions referenced in admin.py:', missingFunctions.output);
        
        console.log('\\n=== CHECKING IF FUNCTIONS EXIST ELSEWHERE ===');
        const findFunctions = await executeCommand(`cd /root/psvibe-sales-bot && find bot/ -name "*.py" -exec grep -l "def cmd_admin_sal_adv\\|def cmd_admin_pnl\\|def cmd_admin_cashflow\\|def cmd_admin_liability\\|def cmd_admin_bookings\\|def cmd_staff_booking\\|def cmd_confirmed_bookings\\|def show_con_mgmt_menu\\|def cmd_promo_reports" {} \\;`);
        console.log('Files containing these functions:', findFunctions.output);
        
        // The user said the issue is that BTN_STOCK_UPDATE and BTN_ADMIN_ATTEND are "dead" buttons
        // Let me see if they're calling functions that don't exist or are not imported
        
        console.log('\\n=== CHECKING STOCK AND ATTENDANCE FUNCTION CALLS ===');
        
        // Check if show_stock_menu is properly imported and defined
        const stockMenu = await executeCommand(`cd /root/psvibe-sales-bot && grep -n "def show_stock_menu\\|show_stock_menu" bot/handlers/stock.py | head -5`);
        console.log('show_stock_menu definition:', stockMenu.output);
        
        // Check if cmd_setattend is properly imported and defined  
        const setAttend = await executeCommand(`cd /root/psvibe-sales-bot && grep -n "def cmd_setattend\\|cmd_setattend" bot/handlers/attendance.py | head -5`);
        console.log('cmd_setattend definition:', setAttend.output);
        
        // Let me check the actual import section more carefully
        console.log('\\n=== CHECKING IMPORTS IN ADMIN.PY ===');
        const imports = await executeCommand('cd /root/psvibe-sales-bot && head -20 bot/handlers/admin.py');
        console.log('Admin.py imports:', imports.output);
        
        // The issue might be that some functions are referenced but not imported.
        // Let me check what happens when I run a simple test of the admin menu
        
        // Actually, let me first understand what the user means by "dead buttons"
        // Maybe the issue is that the bot is not responding to these button presses
        
        // Let me check if there's a runtime error or if the functions are missing their imports
        console.log('\\n=== LOOKING FOR MISSING FUNCTION IMPORTS ===');
        const checkImports = await executeCommand(`cd /root/psvibe-sales-bot && python3 -c "
from bot.handlers.admin import *
import inspect
try:
    print('show_stock_menu callable:', callable(show_stock_menu))
    print('cmd_setattend callable:', callable(cmd_setattend))
except NameError as e:
    print('NameError:', e)
"`);
        console.log('Import check result:', checkImports.output, checkImports.error);
        
        conn.end();
        
    } catch (error) {
        console.error('Error:', error);
        conn.end();
    }
}

main();