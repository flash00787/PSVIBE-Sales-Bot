const { Client } = require("ssh2");
const conn = new Client();
conn.on("ready", () => {
  conn.exec("curl -s localhost:8000/openapi.json 2>/dev/null | python3 -c \"import json,sys; d=json.load(sys.stdin); [print(k) for k in d.get('paths',{}).keys()]\" 2>/dev/null || echo 'NO_OPENAPI'; echo '==='; ls /root/psvibe-sale-bot/bot/handlers/ 2>/dev/null; echo '==='; ls /root/psvibe-sale-bot/customer_bot/ 2>/dev/null; echo '==='; grep -c 'def api_' /root/psvibe-sale-bot/bot/api_client.py 2>/dev/null", (err, stream) => {
    let out = "";
    stream.on("data", (d) => (out += d));
    stream.on("close", () => { console.log(out); conn.end(); });
  });
});
conn.connect({
  host: "5.223.81.16", port: 22, username: "root",
  privateKey: require("fs").readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa"),
  readyTimeout: 5000
});
