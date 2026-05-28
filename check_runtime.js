const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  conn.exec('echo "=== RUNNING PROCESS ==="; ps aux | grep "[p]ython3.*main.py"; echo "=== LOG SINCE 04:19 ==="; grep "04:19" /root/Sales-Tele-Bot_refactored/logs/bot.log; echo "=== API TEST ==="; curl -s -H "X-API-Key: test" https://ps-vibe.com/api/healthz; echo ""; echo "=== CONFIG ENDPOINT ==="; curl -s -o /dev/null -w "%{http_code}" https://ps-vibe.com/api/sheets/config 2>/dev/null; echo ""', (err, stream) => {
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
