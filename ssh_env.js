const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  const cmds = [
    'cat /etc/psvibe/secrets.env 2>/dev/null | grep API_KEY',
    'cat /etc/psvibe/secrets.env 2>/dev/null | head -5',
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
