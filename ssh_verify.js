const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();

conn.on('ready', () => {
  const cmds = [
    'grep -n -B1 -A1 "consoleType.*_ctype" /root/psvibe_api_server/app.py',
    'curl -s --max-time 5 "http://localhost:8000/api/bookings/search?telegram_chat_id=6296803251" -H "X-API-Key: JWIErd…D-AQ" | python3 -m json.tool 2>/dev/null | head -25',
    'systemctl is-active psvibe-api psvibe_customer_bot',
  ];
  let pending = cmds.length, results = {};
  cmds.forEach((c,i) => {
    conn.exec(c, (err, s) => {
      if (err) { results[i]=err.message; if(--pending===0) done(); return; }
      let d=''; s.on('data',c=>d+=c); s.stderr.on('data',c=>d+=c);
      s.on('close',()=>{results[i]=d; if(--pending===0) done();});
    });
  });
  function done() { cmds.forEach((c,i)=>{ console.log('=== CMD '+i+' ===\n'+results[i]); }); conn.end(); }
});
conn.connect({host:'5.223.81.16',port:22,username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),readyTimeout:15000});
