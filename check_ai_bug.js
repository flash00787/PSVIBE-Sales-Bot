const { Client } = require("ssh2");
const conn = new Client();
conn.on("ready", () => {
  conn.exec('sed -n "235,245p" /root/psvibe-sale-bot/customer_bot/ai.py 2>/dev/null && echo "===" && sed -n "135,145p" /root/psvibe-sale-bot/customer_bot/data/prompts.py 2>/dev/null', (err, stream) => {
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
