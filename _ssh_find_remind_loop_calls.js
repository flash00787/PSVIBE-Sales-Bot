const {Client} = require("ssh2");
const fs = require("fs");
const c = new Client();
c.on("ready", function() {
  // Find where _remind_loop is first called (session start)
  c.exec("grep -n 'create_task.*_remind_loop\\|_remind_loop(' /root/psvibe-sales-bot/bot/handlers/booking_flow.py | head -10", function(err, stream) {
    let out = "";
    stream.on("data", function(d) { out += d.toString(); });
    stream.stderr.on("data", function(d) { out += d.toString(); });
    stream.on("close", function() {
      console.log("_remind_loop calls:", out);
      
      // Also check session_reminder_store for message_thread_id
      c.exec("grep -n 'message_thread_id' /root/psvibe-sales-bot/bot/session_reminder_store.py | head -10", function(e2, s2) {
        let o2 = "";
        s2.on("data", function(d) { o2 += d.toString(); });
        s2.stderr.on("data", function(d) { o2 += d.toString(); });
        s2.on("close", function() {
          console.log("session_reminder_store:", o2);
          
          // Find ALL calls to _remind_loop including in sales.py
          c.exec("grep -rn 'create_task.*_remind_loop\\|_remind_loop(' /root/psvibe-sales-bot/bot/ --include='*.py' | grep -v '.bak' | grep -v '__pycache__' | head -15", function(e3, s3) {
            let o3 = "";
            s3.on("data", function(d) { o3 += d.toString(); });
            s3.stderr.on("data", function(d) { o3 += d.toString(); });
            s3.on("close", function() {
              console.log("ALL:_remind_loop:", o3);
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
setTimeout(function() { process.exit(0); }, 25000);
