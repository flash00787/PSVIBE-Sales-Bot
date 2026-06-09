const { Client } = require("ssh2");
const fs = require("fs");

const conn = new Client();
conn.on("ready", () => {
  const cmds = [
    "grep -n '__all__' /root/staging/bot_src/bot/__init__.py",
    "wc -l /root/staging/bot_src/bot/__init__.py",
    "sed -n '9861,10000p' /root/staging/monolithic_ref/main.py",
  ];
  
  let remaining = cmds.length;
  const results = {};
  
  cmds.forEach((cmd, idx) => {
    conn.exec(cmd, (err, stream) => {
      if (err) { results[idx] = "ERROR: " + err; remaining--; check(); return; }
      let data = "";
      stream.on("data", d => data += d.toString());
      stream.stderr.on("data", d => process.stderr.write(`[${idx}] ${d}`));
      stream.on("close", () => {
        results[idx] = data;
        remaining--;
        check();
      });
    });
  });
  
  function check() {
    if (remaining > 0) return;
    for (let i = 0; i < cmds.length; i++) {
      console.log(`\n=== RESULT ${i} ===`);
      console.log(results[i].substring(0, 6000));
    }
    conn.end();
  }
}).connect({
  host: "167.71.196.120",
  port: 22,
  username: "root",
  privateKey: fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa")
});
