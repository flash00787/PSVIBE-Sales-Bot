const { Client } = require("ssh2");
const fs = require("fs");

const conn = new Client();
conn.on("ready", () => {
  const cmds = [
    "head -50 /root/staging/bot_src/bot/__init__.py",
    "grep -n 'asyncio' /root/staging/bot_src/bot/__init__.py",
    "grep -n 'def prompt_end_session\\|def step_end_session\\|def prompt_book_console\\|def step_book_console' /root/staging/monolithic_ref/main.py",
    "grep -n 'import asyncio' /root/staging/monolithic_ref/main.py | head -3"
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
      console.log(`\n=== CMD ${i}: ${cmds[i].substring(0,60)} ===`);
      console.log(results[i].substring(0, 3000));
    }
    conn.end();
  }
}).connect({
  host: "167.71.196.120",
  port: 22,
  username: "root",
  privateKey: fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa")
});
