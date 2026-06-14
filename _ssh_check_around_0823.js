const {Client} = require("ssh2");
const fs = require("fs");
const c = new Client();
c.on("ready", function() {
  c.exec("grep '2026-06-14 08:2[0-9]' /root/psvibe-sales-bot/bot_status.log | tail -40", function(err, stream) {
    let out = "";
    stream.on("data", function(d) { out += d.toString(); });
    stream.stderr.on("data", function(d) { out += d.toString(); });
    stream.on("close", function() {
      console.log(out);
      c.end();
    });
  });
});
c.on("error", function(e) { console.log("CONN_ERR:", e.message); });
c.connect({host:"5.223.81.16", port:22, username:"root", privateKey:fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa"), readyTimeout:10000});
setTimeout(function() { process.exit(0); }, 20000);
