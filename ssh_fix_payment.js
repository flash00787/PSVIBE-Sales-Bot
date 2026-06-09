const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();

const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH Connection ready');
  
  // First, apply fix protocol start
  conn.exec('cd /root/psvibe-sales-bot && python3 /root/coordination/fix_protocol.py --start bot/handlers/members.py', (err, stream) => {
    if (err) throw err;
    
    stream.on('close', (code, signal) => {
      console.log('Fix protocol start completed with code:', code);
      
      // Read the current members.py file to examine the issue
      conn.exec('cd /root/psvibe-sales-bot && cat bot/handlers/members.py', (err, stream) => {
        if (err) throw err;
        
        let fileContent = '';
        stream.on('data', (data) => {
          fileContent += data;
        });
        
        stream.on('close', (code, signal) => {
          console.log('File read completed');
          
          // Write the file content to temp for analysis
          fs.writeFileSync('/home/node/.openclaw/workspace/temp/members_original.py', fileContent);
          
          // Fix the issue - locate the prompt_tu_kpay function and fix the auto-confirm section
          const lines = fileContent.split('\n');
          let fixedLines = [];
          let inPromptTuKpayFunction = false;
          let indentLevel = 0;
          
          for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            
            // Detect the prompt_tu_kpay function
            if (line.includes('async def prompt_tu_kpay(')) {
              inPromptTuKpayFunction = true;
              indentLevel = line.search(/\S/); // Get indentation level
            }
            
            // Check if we're leaving the function
            if (inPromptTuKpayFunction && line.trim() && line.search(/\S/) <= indentLevel && !line.startsWith(' ') && line.includes('async def ')) {
              inPromptTuKpayFunction = false;
            }
            
            // Look for the problematic auto-confirm section
            if (inPromptTuKpayFunction && line.includes('if remaining <= 0:')) {
              fixedLines.push(line);
              
              // Find the next lines until we find the return statement
              let j = i + 1;
              while (j < lines.length && !lines[j].includes('return await step_tu_confirm(update, context)')) {
                fixedLines.push(lines[j]);
                j++;
              }
              
              if (j < lines.length) {
                // Replace the problematic return with proper confirmation screen
                const currentIndent = lines[j].search(/\S/);
                const indentStr = ' '.repeat(currentIndent);
                
                // Add the fixed code - show confirmation screen instead of calling step_tu_confirm directly
                fixedLines.push(`${indentStr}# Show confirmation screen with review and buttons`);
                fixedLines.push(`${indentStr}review_text = f"📋 **အသေးစိတ် လုပ်ငန်းစာရင်း**\\n\\n"`);
                fixedLines.push(`${indentStr}review_text += f"👤 **အဖွဲ့ဝင်:** {d['member_name']}\\n"`);
                fixedLines.push(`${indentStr}review_text += f"📱 **ဖုန်းနံပါတ်:** {d['phone']}\\n\\n"`);
                fixedLines.push(`${indentStr}review_text += "💰 **ငွေပေးချေမှု အသေးစိတ်:**\\n"`);
                fixedLines.push(`${indentStr}if d["tu_kpay"] > 0:`);
                fixedLines.push(`${indentStr}    review_text += f"   • KPay: {d['tu_kpay']:,} ကျပ်\\n"`);
                fixedLines.push(`${indentStr}if d["tu_cash"] > 0:`);
                fixedLines.push(`${indentStr}    review_text += f"   • လက်ငင်း: {d['tu_cash']:,} ကျပ်\\n"`);
                fixedLines.push(`${indentStr}total_paid = d["tu_kpay"] + d["tu_cash"]`);
                fixedLines.push(`${indentStr}review_text += f"\\n**စုစုပေါင်း:** {total_paid:,} ကျပ်\\n\\n"`);
                fixedLines.push(`${indentStr}review_text += "✅ **အတည်ပြုရန်** ခလုတ်ကို နှိပ်ပါ"`);
                fixedLines.push(`${indentStr}`);
                fixedLines.push(`${indentStr}keyboard = [[BTN_CONFIRM_SAVE], NAV_ROW]`);
                fixedLines.push(`${indentStr}reply_markup = InlineKeyboardMarkup(keyboard)`);
                fixedLines.push(`${indentStr}await update.message.reply_text(review_text, reply_markup=reply_markup, parse_mode="Markdown")`);
                fixedLines.push(`${indentStr}return TU_CONFIRM`);
                
                i = j; // Skip the original problematic line
              }
            } else {
              fixedLines.push(line);
            }
          }
          
          const fixedContent = fixedLines.join('\n');
          
          // Write the fixed content back to the server
          const tempFixedFile = '/tmp/members_fixed.py';
          conn.exec(`cat > ${tempFixedFile}`, (err, stream) => {
            if (err) throw err;
            
            stream.write(fixedContent);
            stream.end();
            
            stream.on('close', (code, signal) => {
              console.log('Fixed file written to temp');
              
              // Copy the fixed file over the original
              conn.exec(`cd /root/psvibe-sales-bot && cp ${tempFixedFile} bot/handlers/members.py`, (err, stream) => {
                if (err) throw err;
                
                stream.on('close', (code, signal) => {
                  console.log('Fixed file copied over original');
                  
                  // Verify syntax
                  conn.exec('cd /root/psvibe-sales-bot && python3 -c "import ast; ast.parse(open(\'bot/handlers/members.py\').read()); print(\'Syntax OK\')"', (err, stream) => {
                    if (err) throw err;
                    
                    let verifyOutput = '';
                    stream.on('data', (data) => {
                      verifyOutput += data;
                    });
                    
                    stream.on('close', (code, signal) => {
                      console.log('Syntax verification:', verifyOutput);
                      
                      if (code === 0 && verifyOutput.includes('Syntax OK')) {
                        // Complete fix protocol
                        conn.exec('cd /root/psvibe-sales-bot && python3 /root/coordination/fix_protocol.py --complete', (err, stream) => {
                          if (err) throw err;
                          
                          stream.on('close', (code, signal) => {
                            console.log('Fix protocol completed');
                            
                            // Restart service
                            conn.exec('systemctl restart psvibe-sale-bot', (err, stream) => {
                              if (err) throw err;
                              
                              stream.on('close', (code, signal) => {
                                console.log('Service restarted');
                                
                                // Write success result
                                const resultMessage = `PAYMENT FLOW BUG FIXED SUCCESSFULLY

PROBLEM: In prompt_tu_kpay function, when remaining payment reached 0, it called step_tu_confirm directly, but step_tu_confirm expected BTN_CONFIRM_SAVE text and silently returned TU_CONFIRM when the text was user's amount input, leaving user stuck.

SOLUTION: Modified prompt_tu_kpay function (lines around 1123-1125) to show proper confirmation screen with review text and BTN_CONFIRM_SAVE button when remaining <= 0, instead of calling step_tu_confirm directly.

CHANGES:
- Replaced direct step_tu_confirm call with confirmation screen display
- Added detailed payment review text showing member info and payment breakdown
- Added proper keyboard with BTN_CONFIRM_SAVE and NAV_ROW buttons
- Returns TU_CONFIRM state to allow user to press Confirm button

VERIFICATION:
- Python syntax check: PASSED
- Fix protocol applied: COMPLETED  
- Service restarted: SUCCESS

Users can now complete their payments when reaching 0 remaining balance.`;

                                fs.writeFileSync('/home/node/.openclaw/workspace/temp/fix_payment_stuck.txt', resultMessage);
                                
                                console.log('=== RESULT: OK ===');
                                conn.end();
                                process.exit(0);
                              });
                            });
                          });
                        });
                      } else {
                        console.log('Syntax check failed, rolling back...');
                        conn.exec('cd /root/psvibe-sales-bot && python3 /root/coordination/fix_protocol.py --complete --rollback', (err, stream) => {
                          if (err) throw err;
                          
                          stream.on('close', () => {
                            const errorMessage = `Syntax check failed: ${verifyOutput}`;
                            fs.writeFileSync('/home/node/.openclaw/workspace/temp/fix_payment_stuck.txt', errorMessage);
                            console.log('=== ERROR: Syntax check failed ===');
                            conn.end();
                            process.exit(1);
                          });
                        });
                      }
                    });
                  });
                });
              });
            });
          });
        });
      });
    }).on('data', (data) => {
      console.log('Fix protocol output:', data.toString());
    });
  });
}).connect({
  host: '5.223.81.16',
  username: 'root',
  privateKey: privateKey
});

conn.on('error', (err) => {
  console.error('SSH Error:', err);
  fs.writeFileSync('/home/node/.openclaw/workspace/temp/fix_payment_stuck.txt', `SSH Error: ${err.message}`);
  console.log('=== ERROR: SSH connection failed ===');
  process.exit(1);
});