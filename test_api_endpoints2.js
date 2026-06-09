const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  conn.exec('API_KEY=$(grep "^API_KEY=" /root/Sales-Tele-Bot_refactored/.env | cut -d= -f2); echo "=== CONFIG ENDPOINT ==="; curl -s -H "X-API-Key: $API_KEY" https://ps-vibe.com/api/sheets/config | head -200; echo ""; echo "=== INVENTORY ==="; curl -s -H "X-API-Key: $API_KEY" https://ps-vibe.com/api/sheets/inventory | head -200', (err, stream) => {
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
