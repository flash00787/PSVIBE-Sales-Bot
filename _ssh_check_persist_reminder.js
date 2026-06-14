const {Client} = require("ssh2");
const fs = require("fs");
const c = new Client();
c.on("ready", function() {
  c.exec("sed -n '65,95p' /root/psvibe-sales-bot/bot/session_reminder_store.py", function(err, stream) {
    let out = "";
    stream.on("data", function(d) { out += d.toString(); });
    stream.stderr.on("data", function(d) { out += d.toString(); });
    stream.on("close", function() {
      console.log("PERSIST_REMINDER:");
      console.log(out);
      
      // Also check the restore function
      c.exec("sed -n '170,195p' /root/psvibe-sales-bot/bot/session_reminder_store.py", function(e2, s2) {
        let o2 = "";
        s2.on("data", function(d) { o2 += d.toString(); });
        s2.stderr.on("data", function(d) { o2 += d.toString(); });
        s2.on("close", function() {
          console.log("RESTORE:");
          console.log(o2);
          c.end();
        });
      });
    });
  });
});
c.on("error", function(e) { console.log("CONN_ERR:", e.message); });
c.connect({host:"5.223.81.16", port:22, username:"root", privateKey:fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa"), readyTimeout:10000});
setTimeout(function() { process.exit(0); }, 25000);
