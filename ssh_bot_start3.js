const { Client } = require("ssh2");
const fs = require("fs");
const c = new Client();
c.on("ready", function() {
  // First convert .env to proper format and source it, then run bot
  this.exec("cd /root/Sales-Tele-Bot && sed 's/^/export /' .env > /tmp/env_export.sh && set -a && source /tmp/env_export.sh && set +a && python3 -c \"import os; print('OK SHEET_ID:', os.environ.get('SHEET_ID','NO'))\" 2>&1", function(e,s) {
    let o=""; s.on("data",d=>o+=d); s.stderr.on("data",d=>o+=d);
    s.on("close",()=>{console.log(o);c.end();});
  });
});
c.on("error", e => { console.log("ERR:", e.message); });
c.connect({ host: "5.223.81.16", port:22, username:"root", privateKey: fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa"), hostVerifier: () => true, readyTimeout:10000 });
