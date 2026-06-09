const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  const cmds = [
    'grep -E "API_BASE|API_KEY" /root/psvibe-sales-bot/customer_bot/api.py 2>/dev/null | head -5',
    'grep -E "API_BASE_URL|API_BASE" /etc/psvibe/secrets.env 2>/dev/null',
    'journalctl -u psvibe_customer_bot --no-pager --since "6 hours ago" 2>&1 | grep -i -E "error|traceback|warning|exception|booking|mybooking|pending" | tail -30',
    'journalctl -u psvibe_customer_bot --no-pager --since "24 hours ago" 2>&1 | grep -i -E "warning.*booking|error.*booking|mybookings|Task was destroyed" | tail -20',
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
