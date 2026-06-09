const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();

conn.on('ready', () => {
  const cmds = [
    // Fix protocol completion
    'cd /root && python3 coordination/fix_protocol.py --complete 2>&1 || echo "fix_protocol not found, skipping"',
    // Restart API server
    'systemctl restart psvibe-api 2>&1 && echo "API restarted" || echo "API restart FAILED"',
    // Restart customer bot  
    'systemctl restart psvibe_customer_bot 2>&1 && echo "Customer bot restarted" || echo "Customer bot restart FAILED"',
    // Wait and check status
    'sleep 3 && systemctl status psvibe-api --no-pager 2>&1 | head -8',
    'systemctl status psvibe_customer_bot --no-pager 2>&1 | head -8',
    // Test the API still works
    'sleep 2 && curl -s "http://localhost:8000/api/bookings/search?telegram_chat_id=6296803251" -H "X-API-Key: JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" | python3 -c "import sys,json; d=json.load(sys.stdin); bks=d.get(\"data\",{}).get(\"bookings\",[]); print(f\"API OK: {len(bks)} bookings\"); [print(f\\\"  #{b[\\\"id\\\"]} status={b[\\\"status\\\"]} consoleType={b.get(\\\"consoleType\\\",\\\"N/A\\\")} console_id={b.get(\\\"console_id\\\",\\\"N/A\\\")}\\\") for b in bks[:3]]" 2>&1',
  ];
  let pending = cmds.length, results = {};
  cmds.forEach((c,i) => {
    conn.exec(c, (err, s) => {
      if (err) { results[i]=err.message; if(--pending===0) done(); return; }  
      let d=''; s.on('data',c=>d+=c); s.stderr.on('data',c=>d+=c);
      s.on('close',()=>{results[i]=d; if(--pending===0) done();});
    });
  });
  function done() { cmds.forEach((c,i)=>{ console.log('=== CMD '+i+': '+c+' ===\n'+results[i]); }); conn.end(); }
});
conn.connect({host:'5.223.81.16',port:22,username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),readyTimeout:15000});
