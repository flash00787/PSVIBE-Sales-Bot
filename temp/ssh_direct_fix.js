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
        // Read current members.py
        console.log('=== Reading current members.py ===');
        const readResult = await execCommand('cat /root/psvibe-sales-bot/bot/handlers/members.py');
        if (readResult.code !== 0) {
            console.error('Failed to read members.py');
            conn.end();
            return;
        }

        const currentContent = readResult.stdout;
        
        // Find the step_tu_kpay function and add the fix
        const lines = currentContent.split('\n');
        let fixedLines = [];
        let inStepTuKpay = false;
        let indentLevel = 0;
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            
            // Detect start of step_tu_kpay function
            if (line.includes('async def step_tu_kpay(')) {
                inStepTuKpay = true;
                indentLevel = line.match(/^\\s*/)[0].length;
                fixedLines.push(line);
                continue;
            }
            
            // Detect end of function (next function or end of file)
            if (inStepTuKpay && line.trim() && line.match(/^\\s*/)[0].length <= indentLevel && 
                (line.includes('async def ') || line.includes('def ') || line.includes('class '))) {
                inStepTuKpay = false;
            }
            
            // Inside step_tu_kpay function - look for the problematic section
            if (inStepTuKpay && line.includes('# Show review (common for both BTN_PAY_DONE and amount parse)')) {
                // Add the fix before the "Show review" section
                const currentIndent = '    ';  // Standard 4-space indent for function body
                fixedLines.push(currentIndent + '# If we reach here and text is not BTN_PAY_DONE, show error');
                fixedLines.push(currentIndent + 'if text != BTN_PAY_DONE:');
                fixedLines.push(currentIndent + '    await update.message.reply_text(');
                fixedLines.push(currentIndent + '        "⚠️ ကျေးဇူးပြု၍ payment method တစ်ခုခုကို ရွေးချယ်ပါ သို့မဟုတ် amount ရိုက်ထည့်ပါ။",');
                fixedLines.push(currentIndent + '        parse_mode="Markdown"');
                fixedLines.push(currentIndent + '    )');
                fixedLines.push(currentIndent + '    return TU_KPAY');
                fixedLines.push('');
                fixedLines.push(line); // Add the original comment
                continue;
            }
            
            fixedLines.push(line);
        }
        
        const fixedContent = fixedLines.join('\\n');
        
        // Write the fixed content to a temporary file first
        const writeCmd = `cat > /tmp/members_fixed.py << 'EOF'
${fixedContent}
EOF`;
        
        console.log('=== Writing fixed content ===');
        const writeResult = await execCommand(writeCmd);
        if (writeResult.code !== 0) {
            console.error('Failed to write fixed file:', writeResult.stderr);
            conn.end();
            return;
        }
        
        // Test the syntax
        console.log('=== Testing syntax ===');
        const syntaxResult = await execCommand('cd /root/psvibe-sales-bot && python3 -m py_compile /tmp/members_fixed.py');
        if (syntaxResult.code !== 0) {
            console.error('Syntax error in fixed file:', syntaxResult.stderr);
            conn.end();
            return;
        }
        
        // Copy the fixed file over the original
        console.log('=== Applying fix ===');
        const copyResult = await execCommand('cp /tmp/members_fixed.py /root/psvibe-sales-bot/bot/handlers/members.py');
        if (copyResult.code !== 0) {
            console.error('Failed to apply fix:', copyResult.stderr);
            conn.end();
            return;
        }
        
        console.log('✅ Fix applied successfully');
        
        // Run tests
        console.log('=== Running tests ===');
        const testResult1 = await execCommand('cd /root/psvibe-sales-bot && python3 -m pytest tests/test_members.py -x --tb=short');
        console.log('Members tests:', testResult1.stdout, testResult1.stderr);
        
        const testResult2 = await execCommand('cd /root/psvibe-sales-bot && python3 -m pytest tests/test_sales.py -x --tb=short');
        console.log('Sales tests:', testResult2.stdout, testResult2.stderr);

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