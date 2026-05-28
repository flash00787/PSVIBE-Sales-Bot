const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  conn.exec('echo "=== SERVICE ==="; systemctl is-active psvibe-bot-refactored.service; echo "=== LOG LATEST ==="; tail -15 /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null; echo "=== API TEST ==="; curl -s -o /dev/null -w "%{http_code}" https://ps-vibe.com/api/healthz 2>/dev/null; echo ""; echo "=== PROCESS ==="; ps aux | grep "Sales-Tele-Bot_refactored/main.py" | grep -v grep', (err, stream) => {
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
