const { Client } = require('ssh2');
const fs = require('fs');

// STEP 1: Add `from bot import *` at end of handlers/__init__.py
// STEP 2: Test imports work
// STEP 3: Deploy

const conn = new Client();
conn.on('ready', () => {
  // First, read current handlers/__init__.py last 5 lines
  conn.exec('tail -5 /root/staging/bot_src/bot/handlers/__init__.py', (err, stream) => {
    if (err) { console.log("ERR:", err.message); conn.end(); return; }
    let out = "";
    stream.on("data", d => out += d);
    stream.on("close", () => {
      console.log("Current end of handlers/__init__.py:");
      console.log(out);
      
      // Now add `from bot import *` at the end
      // Using sed to append the import
      conn.exec("echo '' >> /root/staging/bot_src/bot/handlers/__init__.py; echo '# Re-export bot-level helpers so handlers can call API functions' >> /root/staging/bot_src/bot/handlers/__init__.py; echo 'from bot import *  # noqa: F401,F403' >> /root/staging/bot_src/bot/handlers/__init__.py; echo 'DONE'", (err2, stream2) => {
        if (err2) { console.log("ERR2:", err2.message); conn.end(); return; }
        let out2 = "";
        stream2.on("data", d => out2 += d);
        stream2.on("close", () => {
          console.log("Add result:", out2);
          
          // Verify the change
          conn.exec("tail -5 /root/staging/bot_src/bot/handlers/__init__.py", (err3, stream3) => {
            if (err3) { console.log("ERR3:", err3.message); conn.end(); return; }
            let out3 = "";
            stream3.on("data", d => out3 += d);
            stream3.on("close", () => {
              console.log("NEW end of handlers/__init__.py:");
              console.log(out3);
              
              // Test imports
              conn.exec("cd /root/staging/bot_src && python3 -c \"import ast; ast.parse(open('bot/handlers/__init__.py').read()); print('SYNTAX OK')\" 2>&1", (err4, stream4) => {
                let out4 = "";
                stream4.on("data", d => out4 += d);
                stream4.on("close", () => {
                  console.log("Syntax check:", out4);
                  
                  // Now do the same for refactored directory
                  conn.exec("echo '' >> /root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py; echo '# Re-export bot-level helpers' >> /root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py; echo 'from bot import *  # noqa: F401,F403' >> /root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py; echo 'DONE'", (err5, stream5) => {
                    let out5 = "";
                    stream5.on("data", d => out5 += d);
                    stream5.on("close", () => {
                      console.log("Refactored add result:", out5);
                      
                      // Test import in refactored
                      conn.exec("cd /root/Sales-Tele-Bot_refactored && python3 -c \"from bot.handlers import *; from bot import _replit_get; print('_replit_get accessible:', _replit_get); print('IMPORTS OK: Handlers + Bot functions accessible')\" 2>&1", (err6, stream6) => {
                        let out6 = "";
                        stream6.on("data", d => out6 += d);
                        stream6.on("close", () => {
                          console.log("Import test result:");
                          console.log(out6);
                          
                          // Restart service
                          conn.exec("systemctl restart psvibe-bot-refactored.service && sleep 5 && systemctl is-active psvibe-bot-refactored.service", (err7, stream7) => {
                            let out7 = "";
                            stream7.on("data", d => out7 += d);
                            stream7.on("close", () => {
                              console.log("Service restart:", out7);
                              
                              // Check log for startup errors
                              conn.exec("tail -20 /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null", (err8, stream8) => {
                                let out8 = "";
                                stream8.on("data", d => out8 += d);
                                stream8.on("close", () => {
                                  console.log("Bot log tail:");
                                  console.log(out8);
                                  conn.end();
                                  process.exit(0);
                                });
                              });
                            });
                          });
                        });
                      });
                    });
                  });
                });
              });
            });
          });
        });
      });
    });
  });
}).on("error", e => console.log("CONN_ERR:", e.message))
.connect({
  host: "167.71.196.120",
  username: "root",
  privateKey: fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa")
});
