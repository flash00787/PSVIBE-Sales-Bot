const { Client } = require("ssh2");
const fs = require("fs");

const files = [
  "/root/staging/bot_src/bot/handlers/console.py",
  "/root/staging/bot_src/bot/handlers/console_mgmt.py",
  "/root/staging/bot_src/bot/handlers/games.py",
  "/root/staging/bot_src/bot/handlers/ginst.py",
];

const conn = new Client();
const results = {};

conn.on("ready", () => {
  let remaining = files.length;
  files.forEach((path) => {
    conn.exec(`cat "${path}" 2>/dev/null || echo "FILE_NOT_FOUND"`, (err, stream) => {
      if (err) { results[path] = "ERROR: " + err.message; remaining--; checkDone(); return; }
      let data = "";
      stream.on("data", (d) => data += d.toString());
      stream.stderr.on("data", (d) => process.stderr.write(`[${path}] ${d}`));
      stream.on("close", () => {
        results[path] = data;
        remaining--;
        checkDone();
      });
    });
  });

  function checkDone() {
    if (remaining > 0) return;
    for (const [path, content] of Object.entries(results)) {
      const fname = path.split("/").pop();
      console.log(`\n===== ${fname} (${content.length} bytes) =====`);
      console.log(content.substring(0, 500));
      console.log("...[truncated, writing full file]...");
      fs.writeFileSync(`/home/node/.openclaw/workspace/v2_${fname}`, content);
    }
    conn.end();
  }
}).connect({
  host: "167.71.196.120",
  port: 22,
  username: "root",
  privateKey: fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa")
});
