const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();

conn.on('ready', () => {
  conn.exec('grep -n -A 15 "for r in rows:" /root/psvibe_api_server/app.py | head -60', (err, s) => {
    let d=''; s.on('data',c=>d+=c);
    s.on('close',()=>{
      console.log('LOOPS:\n'+d);
      
      // Also check for _ctype usage
      conn.exec('grep -n "_ctype" /root/psvibe_api_server/app.py', (e2, s2) => {
        let d2=''; s2.on('data',c=>d2+=c);
        s2.on('close',()=>{
          console.log('_CTYPE:\n'+d2);
          
          // Check the search endpoint specifically
          conn.exec('sed -n "1290,1360p" /root/psvibe_api_server/app.py', (e3, s3) => {
            let d3=''; s3.on('data',c=>d3+=c);
            s3.on('close',()=>{
              console.log('SEARCH ENDPOINT (1290-1360):\n'+d3);
              conn.end();
            });
          });
        });
      });
    });
  });
});
conn.connect({host:'5.223.81.16',port:22,username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),readyTimeout:15000});
