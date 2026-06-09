const { Client } = require("ssh2");
const fs = require("fs");
const c = new Client();

// Step 1: Pre-process .env file and create proper startup script
const script = `#!/bin/bash
cd /root/Sales-Tele-Bot
# Kill old bots
pkill -9 -f "python3.*main" 2>/dev/null
pkill -9 -f "python3.*customer_bot" 2>/dev/null
sleep 1
# Export env vars properly
sed 's/^/export /' .env > /tmp/e.sh
set -a
source /tmp/e.sh
set +a
# Start Staff Bot
nohup .venv/bin/python3 main.py >> main.log 2>&1 &
echo "STAFF=$!"
sleep 4
# Start Customer Bot
nohup .venv/bin/python3 customer_bot.py >> customer.log 2>&1 &
echo "CUST=$!"
sleep 3
# Show status
echo "==RUNNING=="
ps aux | grep python3 | grep -v grep | grep -v unattend
echo "==STAFF_LOG_LAST=="
tail -3 main.log 2>/dev/null
echo "==CUST_LOG_LAST=="
tail -3 customer.log 2>/dev/null
`;

c.on("ready", function() {
  c.exec("cat > /root/start_bots2.sh", function(e,s) {
    if (e) { console.log("ERR:", e.message); c.end(); return; }
    s.stdin.write(script);
    s.stdin.end();
    let o="";
    s.on("data", d => o += d.toString());
    s.stderr.on("data", d => o += d.toString());
    s.on("close", () => {
      console.log("SCRIPT_WRITTEN");
      c.end();
    });
  });
});
c.on("error", e => { console.log("ERR:", e.message); c.end(); });
c.connect({ host: "5.223.81.16", port:22, username:"root", privateKey: fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa"), hostVerifier: () => true, readyTimeout:10000 });
