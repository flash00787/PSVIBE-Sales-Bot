const {Client} = require("ssh2");
const fs = require("fs");
const c = new Client();
c.on("ready", function() {
  c.exec("grep -rn 'def persist_reminder\\|def save_reminder\\|def store_reminder' /root/psvibe-sales-bot/bot/ --include='*.py' | grep -v '.bak' | grep -v '__pycache__'", function(err, stream) {
    let out = "";
    stream.on("data", function(d) { out += d.toString(); });
    stream.stderr.on("data", function(d) { out += d.toString(); });
    stream.on("close", function() {
      console.log(out || "NOT_FOUND");
      
      // Also check the import
      c.exec("grep -rn 'from.*import.*persist_reminder' /root/psvibe-sales-bot/bot/ --include='*.py' | grep -v '.bak' | grep -v '__pycache__'", function(e2, s2) {
        let o2 = "";
        s2.on("data", function(d) { o2 += d.toString(); });
        s2.stderr.on("data", function(d) { o2 += d.toString(); });
        s2.on("close", function() {
          console.log("IMPORTS:", o2 || "NOT_FOUND");
          c.end();
        });
      });
    });
  });
});
c.on("error", function(e) { console.log("CONN_ERR:", e.message); });
c.connect({host:"5.223.81.16", port:22, username:"root", privateKey:fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa"), readyTimeout:10000});
setTimeout(function() { process.exit(0); }, 20000);
