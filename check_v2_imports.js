const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  conn.exec('grep -n "^from \\|^import " /root/Sales-Tele-Bot_refactored/bot/__init__.py | head -30', (err, stream) => {
    if (err) { console.log("ERR:", err.message); conn.end(); return; }
    let out = "";
    stream.on("data", d => out += d);
    stream.on("close", () => { console.log(out); conn.end(); process.exit(0); });
  });
}).on("error", e => console.log("CONN_ERR:", e.message))
.connect({
  host: "167.71.196.120",
  username: "root",
  privateKey: fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa")
});
