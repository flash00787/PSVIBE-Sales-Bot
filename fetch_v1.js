const { Client } = require("ssh2");
const fs = require("fs");

const conn = new Client();
conn.on("ready", () => {
  // First: get function line numbers
  const cmd1 = "grep -n 'def ' /root/staging/monolithic_ref/main.py | grep -i 'console\\|game\\|ginst'";
  conn.exec(cmd1, (err, stream) => {
    if (err) { console.error("Exec error:", err); process.exit(1); }
    let output = "";
    stream.on("data", d => output += d.toString());
    stream.stderr.on("data", d => process.stderr.write(d));
    stream.on("close", (code) => {
      console.log("=== V1 FUNCTION LIST ===");
      console.log(output);
      const lines = output.trim().split("\n").filter(l => l.trim());
      if (lines.length === 0) {
        console.log("No functions found.");
        conn.end();
        return;
      }
      // Get all the functions - we need their full bodies
      // Read the entire range from first to last function with extra context
      const lineNums = lines.map(l => parseInt(l.split(":")[0]));
      const start = Math.max(1, lineNums[0] - 5);
      const end = lineNums[lineNums.length - 1] + 100;
      console.log(`\n=== Reading lines ${start}-${end} ===`);
      
      const cmd2 = `sed -n '${start},${end}p' /root/staging/monolithic_ref/main.py`;
      conn.exec(cmd2, (err2, stream2) => {
        if (err2) { console.error("Exec error:", err2); process.exit(1); }
        let code = "";
        stream2.on("data", d => code += d.toString());
        stream2.on("close", () => {
          fs.writeFileSync("/home/node/.openclaw/workspace/v1_console_games.txt", code);
          console.log("Wrote", code.length, "bytes to v1_console_games.txt");
          console.log("=== FIRST 3000 CHARS ===");
          console.log(code.substring(0, 3000));
          conn.end();
        });
      });
    });
  });
}).connect({
  host: "167.71.196.120",
  port: 22,
  username: "root",
  privateKey: fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa")
});
