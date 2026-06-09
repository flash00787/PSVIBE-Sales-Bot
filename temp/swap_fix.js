const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  // Read full file to work with exact content
  conn.exec('cat /root/psvibe-sales-bot/bot/handlers/members.py', (err, stream) => {
    if (err) { console.error('ERROR:', err); conn.end(); return; }
    let content = '';
    stream.on('data', (d) => { content += d.toString(); });
    stream.on('close', () => {
      console.log('File length:', content.length);
      
      // Block A: BTN_PAY_DONE check (to move after amount parsing)
      const blockA = `    # Check if text is BTN_PAY_DONE
    if text == BTN_PAY_DONE:
        payments = d.get("tu_payments", {})
        psf = sum(payments.values())
        if psf <= 0:
            await update.message.reply_text("\\u26a0\\ufe0f \\u1021\\u1014\\u102c\\u100a\\u1036\\u1006\\u1031\\u1038 payment method \\u1010\\u1005\\u1039 \\u1011\\u102d\\u1004\\u1039\\u1015\\u102b\\u1038 -")
            return await prompt_tu_kpay(update, context)
        d["tu_kpay"] = payments.get("KPay", 0)
        d["tu_cash"] = payments.get("Cash", 0)

`;

      // Block B separator (blank line between blocks)
      const blockSeparator = `    # Try to parse as amount for current method
    try:
        method_amt = int(text.replace(",", "").strip())
    except ValueError:
        await update.message.reply_text("\\u26a0\\ufe0f \\u1002\\u1014\\u103a\\u1000\\u103e\\u1019\\u103a\\u1001\\u1005\\u1037\\u1001\\u1005\\u1037 \\u101b\\u102d\\u102f\\u1000\\u103a\\u1015\\u102b -")
        return TU_KPAY

    current_method = d.get("tu_current_pay_method", "")
    if not current_method:
        return await prompt_tu_kpay(update, context)

    psf = sum(d.get("tu_payments", {}).values())
    rem = amt - psf
    if method_amt < 0 or method_amt > rem:
        await update.message.reply_text(
            f"\\u26a0\\ufe0f 0 \\u1014\\u101c\\u1039 {rem:,} \\u1000\\u1032 \\u1014\\u1031\\u1000\\u103a \\u1002\\u1014\\u103a\\u1000\\u103e  \\u101b\\u102d\\u102f\\u1000\\u103a\\u1015\\u102b -",
            parse_mode="Markdown",
        )
        return TU_KPAY

    if "tu_payments" not in d:
        d["tu_payments"] = {}
    d["tu_payments"][current_method] = method_amt
    return await prompt_tu_kpay(update, context)

`;

      // The review comment that currently follows amount parsing, will follow BTN_PAY_DONE
      const reviewComment = `    # Show review (common for both BTN_PAY_DONE and amount parse)`;
      
      // Verify all blocks are found
      let posA = content.indexOf(blockA);
      let posB = content.indexOf(blockSeparator, posA + blockA.length);
      
      if (posA === -1) { console.error('Block A not found!'); conn.end(); return; }
      if (posB === -1) { console.error('Block B not found!'); conn.end(); return; }
      
      console.log('Block A pos:', posA, 'len:', blockA.length);
      console.log('Block B pos:', posB, 'len:', blockSeparator.length);
      
      // Current ordering: A + B
      // Desired ordering: B + A
      // So replace AB with BA
      let beforeA = content.substring(0, posA);
      let afterB = content.substring(posB + blockSeparator.length);
      
      let newContent = beforeA + blockSeparator + blockA + afterB;
      
      console.log('New length:', newContent.length, '(was:', content.length, ')');
      
      // Verify the swap
      let posBnew = newContent.indexOf(blockSeparator);
      let posAnew = newContent.indexOf(blockA, posBnew + blockSeparator.length);
      console.log('New positions - B:', posBnew, 'A:', posAnew);
      
      if (posBnew === -1 || posAnew === -1) {
        console.error('Swap verification failed!');
        conn.end();
        return;
      }
      if (posBnew >= posAnew) {
        console.error('B is not before A!');
        conn.end();
        return;
      }
      
      // Write
      const b64 = Buffer.from(newContent).toString('base64');
      conn.exec(`echo '${b64}' | base64 -d > /root/psvibe-sales-bot/bot/handlers/members.py`, (err2, wstream) => {
        if (err2) { console.error('WRITE ERR:', err2); conn.end(); return; }
        let werr = '';
        wstream.stderr.on('data', (d) => { werr += d.toString(); });
        wstream.on('close', (code) => {
          console.log('Write exit:', code, werr || '(none)');
          
          // Verify syntax
          conn.exec('cd /root/psvibe-sales-bot && python3 -c "import ast; ast.parse(open(\'bot/handlers/members.py\').read()); print(\'SYNTAX OK\')"', (err3, vstream) => {
            if (err3) { console.error('VERIFY ERR:', err3); conn.end(); return; }
            let vout = '';
            vstream.on('data', (d) => { vout += d.toString(); });
            vstream.stderr.on('data', (d) => { console.error('VSTDERR:', d.toString()); });
            vstream.on('close', (code3) => {
              console.log('Syntax:', vout.trim(), 'exit:', code3);
              
              // Show the fixed area
              conn.exec("grep -n 'def step_tu_kpay\\|def step_tu_confirm\\|return TU_CONFIRM\\|# Try to parse as amount\\|# Check if text is BTN_PAY_DONE\\|# Show review (common for both' /root/psvibe-sales-bot/bot/handlers/members.py | grep -A1 -B1 'step_tu_kpay\\|step_tu_confirm' | head -20; echo '---'; sed -n '1180,1220p' /root/psvibe-sales-bot/bot/handlers/members.py", (err4, s4) => {
                if (err4) { console.error('ERR4:', err4); conn.end(); return; }
                let o4 = '';
                s4.on('data', (d) => { o4 += d.toString(); });
                s4.on('close', () => {
                  console.log('=== FINAL VERIFY ===');
                  console.log(o4);
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

conn.on('error', (err) => { console.error('SSH ERROR:', err); });

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: privateKey,
  readyTimeout: 30000,
});
