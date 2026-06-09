const { Client } = require("ssh2");
const conn = new Client();
conn.on("ready", () => {
  conn.exec("echo 'SSH_OK' && grep -c 'set(result.get' /root/psvibe-sale-bot/bot/__init__.py", (err, stream) => {
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
