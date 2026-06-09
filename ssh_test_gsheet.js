const { Client } = require("ssh2");
const fs = require("fs");
const c = new Client();

const pyScript = `
import gspread
import os
gc = gspread.service_account(filename="service_account.json")
print("GC_OK")
sh = gc.open_by_key(os.environ["SHEET_ID"])
print("SHEET_TITLE:", sh.title)
ws = sh.sheet1
print("ROWS:", ws.row_count, "COLS:", ws.col_count)
`;

c.on("ready", function() {
  c.exec("cd /root/Sales-Tele-Bot; set -a; source /tmp/e.sh 2>/dev/null; set +a; timeout 15 .venv/bin/python3 -c '" + pyScript.replace(/\n/g, ";") + "' 2>&1", function(e,s) {
    let o=""; s.on("data",d=>o+=d); s.stderr.on("data",d=>o+=d);
    s.on("close",()=>{console.log(o);c.end();});
  });
});
c.on("error", e => { console.log("ERR:", e.message); });
c.connect({ host: "5.223.81.16", port:22, username:"root", privateKey: fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa"), hostVerifier: () => true, readyTimeout:10000 });
