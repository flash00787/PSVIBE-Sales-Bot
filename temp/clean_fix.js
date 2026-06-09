const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

// Read original file content FIRST to build exact replacements
conn.on('ready', () => {
  console.log('SSH connected');
  
  conn.exec('cat /root/psvibe-sales-bot/bot/handlers/members.py', (err, stream) => {
    if (err) { console.error('ERROR:', err); conn.end(); return; }
    let content = '';
    stream.on('data', (d) => { content += d.toString(); });
    stream.on('close', () => {
      console.log('File length:', content.length);
      
      // The dead code block to move - from right after return TU_CONFIRM
      const returnConfirm = '    return TU_CONFIRM\n';
      const deadMarker = '\n    # Try to parse as amount for current method';
      const nextFuncMarker = '\n@log_duration("members:step_tu_confirm")';
      
      // Find return TU_CONFIRM
      let rci = content.indexOf(returnConfirm);
      if (rci === -1) { console.error('Cannot find return TU_CONFIRM'); conn.end(); return; }
      
      // Find dead code start (the comment after return TU_CONFIRM)
      let deadStart = content.indexOf(deadMarker, rci);
      if (deadStart === -1) { console.error('Cannot find dead code start'); conn.end(); return; }
      deadStart++; // skip the leading \n
      
      // Find dead code end (next function marker after dead code start)
      let deadEnd = content.indexOf(nextFuncMarker, deadStart);
      if (deadEnd === -1) { console.error('Cannot find dead code end'); conn.end(); return; }
      deadEnd++; // skip the leading \n
      
      const deadBlock = content.substring(deadStart, deadEnd);
      console.log('Dead block length:', deadBlock.length);
      console.log('Dead block starts with:', deadBlock.substring(0, 60));
      console.log('Dead block ends with:', deadBlock.substring(deadBlock.length - 60));
      
      // Find insertion point: right after BTN_PAY_DONE section, before review
      const insertAfter = '        d["tu_cash"] = payments.get("Cash", 0)\n';
      const insertBefore = '\n    # Show review (common for both BTN_PAY_DONE and amount parse)';
      
      let insertIdx = content.indexOf(insertAfter);
      if (insertIdx === -1) { 
        console.error('Cannot find insertion point "d[tu_cash]"'); 
        conn.end(); return; 
      }
      insertIdx += insertAfter.length;
      
      // Verify insertBefore follows
      let checkBefore = content.indexOf(insertBefore, insertIdx);
      if (checkBefore !== insertIdx) {
        console.error('Insertion point not followed by review comment. Found at:', checkBefore, 'expected:', insertIdx);
        console.error('Content at insertIdx:', JSON.stringify(content.substring(insertIdx, insertIdx+100)));
        conn.end(); return;
      }
      
      // Build new content:
      // 1. Everything up to deadStart (includes return TU_CONFIRM and following blank lines)
      // 2. Skip deadBlock
      // 3. Everything from deadEnd to end
      let withoutDead = content.substring(0, deadStart) + content.substring(deadEnd);
      
      // Now insert deadBlock before review section
      // Find insertion point in the modified content
      let insertIdx2 = withoutDead.indexOf(insertAfter);
      insertIdx2 += insertAfter.length;
      
      let newContent = withoutDead.substring(0, insertIdx2) + '\n' + deadBlock + withoutDead.substring(insertIdx2);
      
      console.log('Original length:', content.length);
      console.log('New length:', newContent.length);
      
      // Write back via base64
      const b64 = Buffer.from(newContent).toString('base64');
      const writeCmd = `echo '${b64}' | base64 -d > /root/psvibe-sales-bot/bot/handlers/members.py`;
      
      conn.exec(writeCmd, (err2, wstream) => {
        if (err2) { console.error('WRITE ERROR:', err2); conn.end(); return; }
        let werr = '';
        wstream.stderr.on('data', (d) => { werr += d.toString(); });
        wstream.on('close', (code) => {
          console.log('Write exit:', code, 'stderr:', werr || '(none)');
          if (code !== 0) { console.error('WRITE FAILED'); conn.end(); return; }
          
          // Verify
          conn.exec('cd /root/psvibe-sales-bot && python3 -c "import ast; ast.parse(open(\'bot/handlers/members.py\').read()); print(\'SYNTAX OK\')"', (err3, vstream) => {
            if (err3) { console.error('VERIFY ERROR:', err3); conn.end(); return; }
            let vout = '';
            vstream.on('data', (d) => { vout += d.toString(); });
            vstream.stderr.on('data', (d) => { console.error('VERIFY STDERR:', d.toString()); });
            vstream.on('close', (code3) => {
              console.log('Verify:', vout.trim(), 'exit:', code3);
              
              // Check the fixed area
              conn.exec("sed -n '1190,1220p' /root/psvibe-sales-bot/bot/handlers/members.py", (err4, s4) => {
                if (err4) { console.error('CHECK ERROR:', err4); conn.end(); return; }
                let o4 = '';
                s4.on('data', (d) => { o4 += d.toString(); });
                s4.on('close', () => {
                  console.log('=== FIX AREA (1190-1220) ===');
                  console.log(o4);
                  
                  // Check around return TU_CONFIRM
                  conn.exec("sed -n '1265,1280p' /root/psvibe-sales-bot/bot/handlers/members.py", (err5, s5) => {
                    if (err5) { console.error('CHECK ERR2:', err5); conn.end(); return; }
                    let o5 = '';
                    s5.on('data', (d) => { o5 += d.toString(); });
                    s5.on('close', () => {
                      console.log('=== AFTER REVIEW (1265-1280) ===');
                      console.log(o5);
                      console.log('=== ALL DONE ===');
                      conn.end();
                    });
                  });
                });
              });
            });
          });
        });
      });
    });
  });
});

conn.on('error', (err) => { console.error('SSH ERROR:', err); });

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: privateKey,
  readyTimeout: 15000,
});
