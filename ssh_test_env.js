const { Client } = require("ssh2");
const fs = require("fs");
const c = new Client();
c.on("ready", function() {
  this.exec("cd /root/Sales-Tele-Bot && pkill -9 -f 'python3.*main.py' 2>/dev/null; sleep 1; .venv/bin/python3 -c 'import os; print(\"SHEET_ID:\", os.environ.get(\"SHEET_ID\", \"NOT_SET\"))'; echo DIRECT_TEST; env SHEET_ID=DIRECT_SET .venv/bin/python3 -c 'import os; print(\"SHEET_ID:\", os.environ.get(\"SHEET_ID\", \"NOT_SET\"))'", function(e,s) {
    let o=""; s.on("data",d=>o+=d); s.stderr.on("data",d=>o+=d);
    s.on("close",()=>{console.log(o);c.end();});
  });
});
c.on("error", e => { console.log("ERR:", e.message); });
c.connect({ host: "5.223.81.16", port:22, username:"root", privateKey: fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa"), hostVerifier: () => true, readyTimeout:10000 });
