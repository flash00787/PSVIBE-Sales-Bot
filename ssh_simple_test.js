const { Client } = require("ssh2");
const fs = require("fs");
const c = new Client();
c.on("ready", function() {
  this.exec("echo HELLO_FROM_VPS", function(e,s) {
    let o=""; 
    s.on("data", d => o += d.toString());
    s.stderr.on("data", d => o += d.toString());
    s.on("close", () => { 
      console.log("OUTPUT_START");
      console.log(o);
      console.log("OUTPUT_END");
      c.end(); 
    });
  });
});
c.on("error", e => { console.log("ERR:", e.message); c.end(); });
c.connect({ host: "5.223.81.16", port:22, username:"root", privateKey: fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa"), hostVerifier: () => true, readyTimeout:10000 });
