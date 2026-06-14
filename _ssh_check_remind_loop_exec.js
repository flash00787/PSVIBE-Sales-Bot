const {Client} = require("ssh2");
const fs = require("fs");
const c = new Client();
c.on("ready", function() {
  c.exec("grep -i 'remind_loop' /root/psvibe-sales-bot/bot_status.log | grep '2026-06-14 0[789]' | tail -20", function(err, stream) {
    let out = "";
    stream.on("data", function(d) { out += d.toString(); });
    stream.stderr.on("data", function(d) { out += d.toString(); });
    stream.on("close", function() {
      console.log("REMIND_LOOP_LOGS:", out || "(none)");
      
      // Also check if there are any async task errors
      c.exec("grep -E 'Task exception.*remind\\|forgotten.*remind\\|remind.*error\\|_remind_loop.*error' /root/psvibe-sales-bot/bot_status.log | head -10", function(e2, s2) {
        let o2 = "";
        s2.on("data", function(d) { o2 += d.toString(); });
        s2.stderr.on("data", function(d) { o2 += d.toString(); });
        s2.on("close", function() {
          console.log("REMIND_ERRORS:", o2 || "(none)");
          
          // Check if _remind_loop even runs (look for "fire_count" or "break")
          c.exec("grep -E 'fire_count|No Timer|still_active|_remind_loop.*exit' /root/psvibe-sales-bot/bot_status.log | head -10", function(e3, s3) {
            let o3 = "";
            s3.on("data", function(d) { o3 += d.toString(); });
            s3.stderr.on("data", function(d) { o3 += d.toString(); });
            s3.on("close", function() {
              console.log("LOOP_INTERNAL:", o3 || "(none)");
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
