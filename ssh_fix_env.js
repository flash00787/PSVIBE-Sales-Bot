const { Client } = require("ssh2");
const fs = require("fs");
const c = new Client();
c.on("ready", function() {
  // Use source + env approach - more reliable
  this.exec("cd /root/Sales-Tele-Bot && bash -c 'source /root/Sales-Tele-Bot/.env 2>/dev/null; python3 -c \"import os; print(\\\"SHEET_ID=\\\", os.environ.get(\\\"SHEET_ID\\\", \\\"NOT_SET\\\")); print(\\\"BOT_TOKEN=\\\", os.environ.get(\\\"BOT_TOKEN\\\", \\\"NOT_SET\\\")[:10])\"'", function(e,s) {
    let o=""; s.on("data",d=>o+=d); s.stderr.on("data",d=>o+=d);
    s.on("close",()=>{console.log(o);c.end();});
  });
});
c.on("error", e => { console.log("ERR:", e.message); });
c.connect({ host: "5.223.81.16", port:22, username:"root", privateKey: fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa"), hostVerifier: () => true, readyTimeout:10000 });
