const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  const cmds = [
    // Check which search endpoint is active by testing the API
    'curl -s "http://localhost:8099/api/bookings/search?telegram_chat_id=6296803251" -H "X-API-Key: $(grep API_KEY /root/psvibe_api_server/.env 2>/dev/null | cut -d= -f2 | tr -d \'"\'")\'"\'" | python3 -m json.tool 2>/dev/null | head -50 || echo "API TEST FAILED"',
    // Full _map_booking_row
    'grep -n -A 50 "def _map_booking_row" /root/psvibe_api_server/patch_routes.py',
    // Check env for API key and port
    'grep -E "API_KEY|API_PORT|port" /root/psvibe_api_server/.env 2>/dev/null | head -5',
    'systemctl status psvibe-api 2>/dev/null | head -10 || supervisorctl status psvibe-api 2>/dev/null | head -5',
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
