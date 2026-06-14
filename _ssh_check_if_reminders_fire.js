const {Client} = require("ssh2");
const fs = require("fs");
const c = new Client();
c.on("ready", function() {
  c.exec("grep -E '_remind_loop|reminder.*text|sendMessage.*Reminder|Session Reminder|session.*remind' /root/psvibe-sales-bot/bot_status.log | grep '2026-06-14 0[789]' | tail -20", function(err, stream) {
    let out = "";
    stream.on("data", function(d) { out += d.toString(); });
    stream.stderr.on("data", function(d) { out += d.toString(); });
    stream.on("close", function() {
      console.log(out || "(empty)");
      
      // More direct check - look for the actually sent reminder messages
      c.exec("grep -B1 '5 မိနစ် ကျန်\\|ဆုံးချိန်ရောက်ပြီ\\|session_reminder_store:' /root/psvibe-sales-bot/bot_status.log | tail -20", function(e2, s2) {
        let o2 = "";
        s2.on("data", function(d) { o2 += d.toString(); });
        s2.stderr.on("data", function(d) { o2 += d.toString(); });
        s2.on("close", function() {
          console.log("REMINDER_TEXT:", o2 || "(none - reminders may not be sending)");
          c.end();
        });
      });
    });
  });
});
c.on("error", function(e) { console.log("CONN_ERR:", e.message); });
c.connect({host:"5.223.81.16", port:22, username:"root", privateKey:fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa"), readyTimeout:10000});
setTimeout(function() { process.exit(0); }, 20000);
