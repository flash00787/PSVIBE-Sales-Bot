const { Client } = require("ssh2");
const conn = new Client();
conn.on("ready", () => {
  conn.exec("systemctl restart psvibe-customer-bot.service; echo 'RESTARTED'", (err, stream) => {
    let out = "";
    stream.on("data", (d) => (out += d));
    stream.stderr.on("data", (d) => (out += d));
    stream.on("close", () => { console.log(out || "done"); conn.end(); });
  });
});
conn.connect({
  host: "5.223.81.16", port: 22, username: "root",
  privateKey: require("fs").readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa"),
  readyTimeout: 5000
});
