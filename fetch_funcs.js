const { Client } = require("ssh2");
const fs = require("fs");

const conn = new Client();
conn.on("ready", () => {
  const cmds = [
    "grep -n 'def show_main_menu\\|def cmd_cancel\\|def show_ssd_menu\\|def _ssd_kb\\|def launch_session_sale\\|def prompt_book_console\\|def step_book_console\\|VALID_CONSOLES =' /root/staging/bot_src/bot/__init__.py",
    "grep -c 'show_main_menu\\|cmd_cancel\\|show_ssd_menu' /root/staging/bot_src/bot/__init__.py",
    // Check all handler files in staging
    "ls -la /root/staging/bot_src/bot/handlers/",
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
      console.log(results[i]);
    }
    conn.end();
  }
}).connect({
  host: "167.71.196.120",
  port: 22,
  username: "root",
  privateKey: fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa")
});
