const {Client} = require("ssh2");
const fs = require("fs");
const c = new Client();
c.on("ready", function() {
  c.exec("grep -E 'Task exception|exception.*_remind|forgotten|Unhandled' /root/psvibe-sales-bot/bot_status.log | grep '2026-06-14 0[789]' | tail -10", function(err, stream) {
    let out = "";
    stream.on("data", function(d) { out += d.toString(); });
    stream.stderr.on("data", function(d) { out += d.toString(); });
    stream.on("close", function() {
      console.log("TASK_EXCEPTIONS:", out || "(none)");
      
      // Check if _remind_loop from booking_flow.py sends messages by looking at sendMessage to staff chat
      c.exec("grep 'sendMessage' /root/psvibe-sales-bot/bot_status.log | grep '2026-06-14 08.*200 OK' | head -10", function(e2, s2) {
        let o2 = "";
        s2.on("data", function(d) { o2 += d.toString(); });
        s2.stderr.on("data", function(d) { o2 += d.toString(); });
        s2.on("close", function() {
          console.log("SENDMESSAGE:", o2 || "(none)");
          
          // Check all sessions currently active (console status)
          c.exec("curl -s http://localhost:8000/api/consoles/status 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); consoles=d.get('data',d.get('consoles',d)) if isinstance(d,dict) else d; [print(f'{c[\\\"id\\\"]}: {c[\\\"status\\\"]} - {c.get(\\\"member\\\",\\\"?\\\")} start={c.get(\\\"start\\\",\\\"?\\\")}') for c in consoles if isinstance(c,dict) and c.get('status')!='Free']\" 2>/dev/null", function(e3, s3) {
            let o3 = "";
            s3.on("data", function(d) { o3 += d.toString(); });
            s3.stderr.on("data", function(d) { o3 += d.toString(); });
            s3.on("close", function() {
              console.log("ACTIVE_SESSIONS:", o3 || "(none or err)");
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
