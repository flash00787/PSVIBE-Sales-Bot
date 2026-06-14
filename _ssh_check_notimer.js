const {Client} = require("ssh2");
const fs = require("fs");
const c = new Client();
c.on("ready", function() {
  // Look at the "No Timer" logic in the code
  c.exec("grep -n '_NO_TIMER_CONSOLES\\|_add_timer\\|_remove_timer\\|No Timer' /root/psvibe-sales-bot/bot/handlers/booking_flow.py | head -15", function(err, stream) {
    let out = "";
    stream.on("data", function(d) { out += d.toString(); });
    stream.stderr.on("data", function(d) { out += d.toString(); });
    stream.on("close", function() {
      console.log(out);
      
      // Find the "No Timer" references in booking.py (where sessions are created)
      c.exec("grep -n '_NO_TIMER_CONSOLES\\|_add_timer\\|_remove_timer\\|No Timer' /root/psvibe-sales-bot/bot/handlers/booking.py | head -10", function(e2, s2) {
        let o2 = "";
        s2.on("data", function(d) { o2 += d.toString(); });
        s2.stderr.on("data", function(d) { o2 += d.toString(); });
        s2.on("close", function() {
          console.log("BOOKING:", o2);
          
          // Check how _add_timer works
          c.exec("grep -n 'def _add_timer\\|def _remove_timer\\|_NO_TIMER' /root/psvibe-sales-bot/bot/__init__.py | head -10", function(e3, s3) {
            let o3 = "";
            s3.on("data", function(d) { o3 += d.toString(); });
            s3.stderr.on("data", function(d) { o3 += d.toString(); });
            s3.on("close", function() {
              console.log("__INIT__:", o3);
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
