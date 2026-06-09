const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  const cmds = [
    'ls /root/psvibe_api_server/patch_routes.py 2>&1',
    'grep -n "bookings.*status\\|@app.*patch\\|@app.*put.*book\\|cancel_booking" /root/psvibe_api_server/app.py /root/psvibe_api_server/patch_routes.py 2>/dev/null | head -20',
    'mysql -u psvibe_user psvibe_api -e "DESC console_booking" 2>/dev/null | head -25',
    'mysql -u psvibe_user psvibe_api -e "SELECT id, console_id, telegram_chat_id, status, booking_date, duration_mins, phone, game_name FROM console_booking WHERE status = \'pending\' LIMIT 3" 2>/dev/null',
    'mysql -u psvibe_user psvibe_api -e "SELECT id, console_id, telegram_chat_id, status, booking_date, duration_mins, phone, game_name FROM console_booking ORDER BY id DESC LIMIT 5" 2>/dev/null',
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
