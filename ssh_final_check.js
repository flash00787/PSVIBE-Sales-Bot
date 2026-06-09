const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();

conn.on('ready', () => {
  conn.exec('grep -n "consoleType\\|raw_console\\|hasattr.*strftime\\|parse_mode.*Markdown" /root/psvibe-sales-bot/customer_bot/booking.py', (err, s) => {
    let d=''; s.on('data',c=>d+=c);
    s.on('close',()=>{
      console.log('BOOKING.PY KEY LINES:\n'+d);
      
      conn.exec('grep -n "consoleType" /root/psvibe_api_server/app.py', (e2, s2) => {
        let d2=''; s2.on('data',c=>d2+=c);
        s2.on('close',()=>{
          console.log('APP.PY consoleType LINES:\n'+d2);
          conn.end();
        });
      });
    });
  });
});
conn.connect({host:'5.223.81.16',port:22,username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),readyTimeout:15000});
