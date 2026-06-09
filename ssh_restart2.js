const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();

conn.on('ready', () => {
  // Restart with timeout
  conn.exec('timeout 15 systemctl restart psvibe-api && echo "API_OK" || echo "API_TIMEOUT"; timeout 10 systemctl restart psvibe_customer_bot && echo "BOT_OK" || echo "BOT_TIMEOUT"', (err, s) => {
    let d=''; s.on('data',c=>d+=c); s.stderr.on('data',c=>d+=c);
    s.on('close',()=>{
      console.log('RESTART:\n'+d);
      // Check status
      conn.exec('systemctl is-active psvibe-api psvibe_customer_bot', (e2, s2) => {
        let d2=''; s2.on('data',c=>d2+=c);
        s2.on('close',()=>{
          console.log('STATUS:\n'+d2);
          // Test API
          conn.exec('curl -s --max-time 5 "http://localhost:8000/api/health"', (e3, s3) => {
            let d3=''; s3.on('data',c=>d3+=c);
            s3.on('close',()=>{
              console.log('HEALTH:\n'+d3);
              conn.end();
            });
          });
        });
      });
    });
  });
});
conn.connect({host:'5.223.81.16',port:22,username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),readyTimeout:15000});
