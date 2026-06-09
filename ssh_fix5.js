const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();

conn.on('ready', () => {
  // Use sed to insert consoleType line into the search endpoint's normalized.append
  conn.exec(`sed -i '/"console_id": r.get("console_id"),$/a\\                "consoleType": _ctype,' /root/psvibe_api_server/app.py`, (err, s) => {
    let d=''; s.on('data',c=>d+=c); s.stderr.on('data',c=>d+=c);
    s.on('close',()=>{
      console.log('SED 1: ' + d.trim() || 'OK');
      
      // Check that we didn't insert too many times
      conn.exec('grep -c \'"consoleType": _ctype\' /root/psvibe_api_server/app.py', (e2, s2) => {
        let d2=''; s2.on('data',c=>d2+=c);
        s2.on('close',()=>{
          console.log('COUNT: ' + d2.trim());
          
          // Verify syntax
          conn.exec('python3 -m py_compile /root/psvibe_api_server/app.py && echo "SYNTAX OK" || echo "SYNTAX FAIL"', (e3, s3) => {
            let d3=''; s3.on('data',c=>d3+=c);
            s3.on('close',()=>{
              console.log('SYNTAX: ' + d3.trim());
              
              // Restart and test
              conn.exec('timeout 15 systemctl restart psvibe-api && sleep 2 && curl -s --max-time 5 "http://localhost:8000/api/bookings/search?telegram_chat_id=6296803251" -H "X-API-Key: JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" | python3 -c "import sys,json; d=json.load(sys.stdin); bks=d.get(\"data\",{}).get(\"bookings\",[]); print(\"BOOKINGS:\", len(bks)); [print(\"  consoleType:\", b.get(\"consoleType\",\"MISSING\"), \"| id:\", b.get(\"id\")) for b in bks[:3]]"', (e4, s4) => {
                let d4=''; s4.on('data',c=>d4+=c);
                s4.on('close',()=>{
                  console.log('TEST:\n'+d4);
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
conn.connect({host:'5.223.81.16',port:22,username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),readyTimeout:15000});
