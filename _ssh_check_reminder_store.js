const {Client} = require("ssh2");
const fs = require("fs");
const c = new Client();
c.on("ready", function() {
  // Check STAFF_NOTIFY_CHAT
  c.exec("grep -rn 'STAFF_NOTIFY_CHAT' /root/psvibe-sales-bot/bot/constants.py | head -5 && echo '===' && grep -n 'STAFF_NOTIFY_CHAT' /root/psvibe-sales-bot/bot/__init__.py | head -5", function(err, stream) {
    let out = "";
    stream.on("data", function(d) { out += d.toString(); });
    stream.stderr.on("data", function(d) { out += d.toString(); });
    stream.on("close", function() {
      console.log(out);
      
      // Check reminder_store.js for persist_reminder
      c.exec("grep -n 'async def persist_reminder' /root/psvibe-sales-bot/bot/handlers/booking_flow.py", function(e2, s2) {
        let o2 = "";
        s2.on("data", function(d) { o2 += d.toString(); });
        s2.stderr.on("data", function(d) { o2 += d.toString(); });
        s2.on("close", function() {
          console.log("persist_reminder location:", o2);
          
          // Check reminder_store.py
          c.exec("grep -n 'def persist_reminder\\|def save_reminder' /root/psvibe-sales-bot/bot/handlers/reminder_store.py 2>/dev/null | head -5", function(e3, s3) {
            let o3 = "";
            s3.on("data", function(d) { o3 += d.toString(); });
            s3.stderr.on("data", function(d) { o3 += d.toString(); });
            s3.on("close", function() {
              console.log("reminder_store:", o3);
              c.end();
            });
          });
        });
      });
    });
  });
});
c.on("error", function(e) { console.log("CONN_ERR:", e.message); });
c.connect({host:"5.223.81.16", port:22, username:"root", privateKey:fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa"), readyTimeout:10000});
setTimeout(function() { process.exit(0); }, 30000);
