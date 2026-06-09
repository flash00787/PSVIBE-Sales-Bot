const { Client } = require("ssh2");
const fs = require("fs");
const c = new Client();
c.on("ready", function() {
  // Convert .env, source it, kill old bots, start new ones
  this.exec("cd /root/Sales-Tele-Bot && pkill -9 -f 'python3.*main.py' 2>/dev/null; pkill -9 -f 'python3.*customer_bot' 2>/dev/null; sleep 1; sed 's/^/export /' .env > /tmp/env_export.sh; set -a; source /tmp/env_export.sh; set +a; nohup .venv/bin/python3 main.py >> /root/Sales-Tele-Bot/main.log 2>&1 & echo STAFF_PID=$!; sleep 4; nohup .venv/bin/python3 customer_bot.py >> /root/Sales-Tele-Bot/customer.log 2>&1 & echo CUSTOMER_PID=$!; sleep 3; echo ---RUNNING---; ps aux | grep python3 | grep -v grep | grep -v unattended || echo NONE_RUNNING; echo ---STAFF_LOG---; tail -3 /root/Sales-Tele-Bot/main.log 2>/dev/null; echo ---CUSTOMER_LOG---; tail -3 /root/Sales-Tele-Bot/customer.log 2>/dev/null", function(e,s) {
    let o=""; s.on("data",d=>o+=d); s.stderr.on("data",d=>o+=d);
    s.on("close",()=>{console.log(o);c.end();});
  });
});
c.on("error", e => { console.log("ERR:", e.message); });
c.connect({ host: "5.223.81.16", port:22, username:"root", privateKey: fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa"), hostVerifier: () => true, readyTimeout:10000 });
