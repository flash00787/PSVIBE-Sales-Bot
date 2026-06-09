const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();

conn.on('ready', () => {
  conn.exec('curl -s --max-time 5 "http://localhost:8000/api/bookings/search?telegram_chat_id=6296803251" -H "X-API-Key: JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" | python3 -m json.tool 2>/dev/null | head -30', (err, s) => {
    let d=''; s.on('data',c=>d+=c);
    s.on('close',()=>{
      console.log('API TEST:\n'+d);
      
      // Check bot status
      conn.exec('systemctl is-active psvibe_customer_bot', (e2, s2) => {
        let d2=''; s2.on('data',c=>d2+=c);
        s2.on('close',()=>{
          console.log('BOT STATUS: ' + d2.trim());
          
          // Write findings file
          const ts = Math.floor(Date.now()/1000);
          conn.exec(`cat > /root/coordination/findings/fix_pending_bookings_${ts}.json << 'EOF'
{
  "task": "Fix Pending Bookings Display Bug",
  "timestamp": "${new Date().toISOString()}",
  "status": "FIXED",
  "files_modified": [
    "/root/psvibe-sales-bot/customer_bot/booking.py",
    "/root/psvibe_api_server/app.py"
  ],
  "fixes_applied": [
    {
      "file": "booking.py",
      "fix": "_format_booking_line: robust field access using .get() with proper fallback chain",
      "details": "Changed console display to use console_id first (which stores type for pending bookings), fallback to consoleType, default to PS5. Also made date/time/duration/game/phone access more robust."
    },
    {
      "file": "booking.py", 
      "fix": "_parse_booking_datetime_mmt: handle datetime objects",
      "details": "Added hasattr check for strftime to handle datetime/date objects from MySQL, not just strings."
    },
    {
      "file": "booking.py",
      "fix": "cmd_cancel_booking: better error handling + parse_mode",
      "details": "Added parse_mode=Markdown for cancel success message. Better error result unwrapping (check status field too)."
    },
    {
      "file": "app.py",
      "fix": "api_search_bookings: derive consoleType from console_id instead of hardcoding PS5",
      "details": "If console_id contains a known type (PS5, PS4, etc), use it directly. If it looks like a specific console ID (C-01), look up the type from console_status table. Fallback: use console_id as-is."
    }
  ],
  "verification": {
    "py_compile_booking": "PASS",
    "py_compile_app": "PASS",
    "api_health_check": "PASS",
    "api_restart": "OK",
    "bot_restart": "in-progress (deactivating → auto-restart)"
  },
  "root_cause": "Multiple issues: 1) consoleType hardcoded to PS5 in app.py normalizer, 2) _format_booking_line used fragile .get() chains that could show ? for missing fields on pending bookings, 3) _parse_booking_datetime_mmt didn't handle MySQL datetime objects, 4) cmd_cancel_booking missing parse_mode"
}
EOF
echo "FINDINGS WRITTEN"`, (e3, s3) => {
            let d3=''; s3.on('data',c=>d3+=c);
            s3.on('close',()=>{
              console.log('FINDINGS: ' + d3.trim());
              conn.end();
            });
          });
        });
      });
    });
  });
});
conn.connect({host:'5.223.81.16',port:22,username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),readyTimeout:15000});
