const { Client } = require("ssh2");
const conn = new Client();
conn.on("ready", () => {
  conn.exec("journalctl -u psvibe-sale-bot.service --since '1 min ago' --no-pager 2>/dev/null | grep -v 'getUpdates\\|HTTP Request'", (err, stream) => {
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
