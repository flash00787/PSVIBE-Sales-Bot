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

function getIndent(line) {
    const match = line.match(/^(\s*)/);
    return match ? match[1].length : 0;
}

async function main() {
    try {
        // Simpler approach - use sed to add the fix
        console.log('=== Applying fix using sed ===');
        
        const fixCommands = [
            // First, let's find the line number with the comment
            `cd /root/psvibe-sales-bot && grep -n "# Show review (common for both BTN_PAY_DONE and amount parse)" bot/handlers/members.py`,
        ];
        
        const grepResult = await execCommand(fixCommands[0]);
        if (grepResult.code !== 0) {
            console.error('Could not find the target line:', grepResult.stderr);
            conn.end();
            return;
        }
        
        const lineNum = parseInt(grepResult.stdout.split(':')[0]);
        console.log(`Found target line at: ${lineNum}`);
        
        // Add the fix before that line
        const sedCommands = [
            `cd /root/psvibe-sales-bot && sed -i '${lineNum}i\\    # If we reach here and text is not BTN_PAY_DONE, show error' bot/handlers/members.py`,
            `cd /root/psvibe-sales-bot && sed -i '${lineNum+1}i\\    if text != BTN_PAY_DONE:' bot/handlers/members.py`,
            `cd /root/psvibe-sales-bot && sed -i '${lineNum+2}i\\        await update.message.reply_text(' bot/handlers/members.py`,
            `cd /root/psvibe-sales-bot && sed -i '${lineNum+3}i\\            "⚠️ ကျေးဇူးပြု၍ payment method တစ်ခုခုကို ရွေးချယ်ပါ သို့မဟုတ် amount ရိုက်ထည့်ပါ။",' bot/handlers/members.py`,
            `cd /root/psvibe-sales-bot && sed -i '${lineNum+4}i\\            parse_mode="Markdown"' bot/handlers/members.py`,
            `cd /root/psvibe-sales-bot && sed -i '${lineNum+5}i\\        )' bot/handlers/members.py`,
            `cd /root/psvibe-sales-bot && sed -i '${lineNum+6}i\\        return TU_KPAY' bot/handlers/members.py`,
            `cd /root/psvibe-sales-bot && sed -i '${lineNum+7}i\\' bot/handlers/members.py`,
        ];
        
        for (const cmd of sedCommands) {
            const result = await execCommand(cmd);
            if (result.code !== 0) {
                console.error(`Failed command: ${cmd}`);
                console.error('Error:', result.stderr);
                conn.end();
                return;
            }
        }
        
        console.log('✅ Fix applied successfully using sed');
        
        // Test the syntax
        console.log('=== Testing syntax ===');
        const syntaxResult = await execCommand('cd /root/psvibe-sales-bot && python3 -m py_compile bot/handlers/members.py');
        if (syntaxResult.code !== 0) {
            console.error('Syntax error in fixed file:', syntaxResult.stderr);
            
            // Show the problematic area
            const showResult = await execCommand(`cd /root/psvibe-sales-bot && sed -n '${lineNum-5},${lineNum+15}p' bot/handlers/members.py`);
            console.log('Problematic area:', showResult.stdout);
            
            conn.end();
            return;
        }
        
        console.log('✅ Syntax check passed');
        
        // Run tests
        console.log('=== Running tests ===');
        const testResult1 = await execCommand('cd /root/psvibe-sales-bot && timeout 30 python3 -m pytest tests/test_members.py -x --tb=short');
        console.log('Members tests result:', testResult1.code === 0 ? 'PASS' : 'FAIL');
        if (testResult1.code !== 0) {
            console.log('Members test output:', testResult1.stdout.substring(0, 1000));
        }
        
        const testResult2 = await execCommand('cd /root/psvibe-sales-bot && timeout 30 python3 -m pytest tests/test_sales.py -x --tb=short');
        console.log('Sales tests result:', testResult2.code === 0 ? 'PASS' : 'FAIL');
        if (testResult2.code !== 0) {
            console.log('Sales test output:', testResult2.stdout.substring(0, 1000));
        }

        console.log('=== Fix Summary ===');
        console.log(`Fixed line: ${lineNum}`);
        console.log('Added validation to prevent random text from advancing to TU_CONFIRM state');
        console.log('Random text now shows error message and stays in TU_KPAY state');

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