const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('Checking current status...');
  
  // Check locks and fix protocol status
  conn.exec('cd /root/psvibe-sales-bot && find . -name "*.lock" -type f && echo "=== LOCKS ABOVE ===" && python3 /root/coordination/fix_protocol.py --status 2>/dev/null || echo "No fix protocol running"', (err, stream) => {
    if (err) throw err;
    
    let statusOutput = '';
    stream.on('data', (data) => {
      statusOutput += data;
    });
    
    stream.on('close', () => {
      console.log('Status check output:', statusOutput);
      
      // Check if the problematic line still exists
      conn.exec('cd /root/psvibe-sales-bot && grep -n "return await step_tu_confirm(update, context)" bot/handlers/members.py', (err, stream) => {
        if (err) {
          console.log('grep command failed, checking if file exists');
          conn.end();
          return;
        }
        
        let grepOutput = '';
        stream.on('data', (data) => {
          grepOutput += data;
        });
        
        stream.on('close', () => {
          console.log('Bug line check:', grepOutput);
          
          const resultMessage = `STATUS CHECK COMPLETED

CURRENT STATE:
Lock status: ${statusOutput}
Bug line check: ${grepOutput ? `STILL EXISTS at ${grepOutput.trim()}` : 'NOT FOUND - may be fixed'}

NEXT STEPS NEEDED:
${grepOutput ? 
  'The problematic line still exists. Manual intervention required to clear locks and apply fix.' : 
  'The bug line is not found. Need to verify if fix was already applied successfully.'}`;

          fs.writeFileSync('/home/node/.openclaw/workspace/temp/fix_payment_stuck.txt', resultMessage);
          console.log('=== STATUS CHECK COMPLETE ===');
          conn.end();
        });
      });
    });
  });
}).connect({
  host: '5.223.81.16',
  username: 'root',
  privateKey: privateKey
});

conn.on('error', (err) => {
  console.error('SSH Error:', err);
  fs.writeFileSync('/home/node/.openclaw/workspace/temp/fix_payment_stuck.txt', `STATUS CHECK FAILED - SSH Error: ${err.message}`);
  console.log('=== ERROR: SSH connection failed ===');
});