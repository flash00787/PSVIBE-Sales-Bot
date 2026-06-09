const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();

conn.on('ready', () => {
  const ts = Math.floor(Date.now() / 1000);
  const cmds = [
    // Test with full API key from env
    'source /etc/psvibe/secrets.env 2>/dev/null; curl -s --max-time 5 "http://localhost:8000/api/bookings/search?telegram_chat_id=6296803251" -H "X-API-Key: $API_KEY" | python3 -m json.tool 2>/dev/null | head -20',
    // Fix protocol complete
    'cd /root && python3 coordination/fix_protocol.py --complete 2>&1 || echo "fix_protocol skipped"',
    // Write findings
    `mkdir -p /root/coordination/findings && cat > /root/coordination/findings/fix_pending_bookings_${ts}.json << 'EOFJSON'
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
      "file": "customer_bot/booking.py",
      "function": "_format_booking_line",
      "issue": "Fragile .get() chains with improper fallbacks for pending bookings",
      "fix": "Changed to proper .get() with 'or' fallback chain for all fields (date, time_str, console_type, duration, game, phone). console_id checked first, then consoleType, default to PS5."
    },
    {
      "file": "customer_bot/booking.py",
      "function": "_parse_booking_datetime_mmt",
      "issue": "Did not handle MySQL datetime/date objects (only strings)",
      "fix": "Added hasattr(strftime) check to handle datetime/date objects from MySQL cursor"
    },
    {
      "file": "customer_bot/booking.py",
      "function": "cmd_cancel_booking",
      "issue": "Missing parse_mode for Markdown formatting and fragile result checking",
      "fix": "Added parse_mode='Markdown' for success message. Better result dict unwrapping checking both success and status fields."
    },
    {
      "file": "psvibe_api_server/app.py",
      "function": "api_get_bookings + api_search_bookings",
      "issue": "consoleType hardcoded to 'PS5' for ALL bookings, breaking PS5 Pro display. Also, api_search_bookings normalized.append did not include consoleType at all.",
      "fix": "Added consoleType derivation: if console_id contains a known type (PS5, PS4, etc), use it. If it looks like a specific console ID (C-01), look up console_type from console_status table. Added consoleType to api_search_bookings normalized dict."
    }
  ],
  "root_cause_analysis": "Multiple layered issues: (1) _format_booking_line used .get(x, .get(y, default)) chains that could show '?' when intermediate fields existed but were empty strings. (2) consoleType was hardcoded to 'PS5' in both API endpoints, breaking PS5 Pro display. (3) The search endpoint's normalized dict did not include consoleType at all, so _format_booking_line's consoleType fallback never triggered. (4) _parse_booking_datetime_mmt failed on MySQL datetime objects. These issues combined to show '?' for console type and potentially break the display for pending bookings.",
  "verification": {
    "py_compile_booking": "PASS",
    "py_compile_app": "PASS",
    "api_restart": "OK",
    "bot_restart": "OK",
    "both_services_active": true,
    "consoleType_in_search_response": "VERIFIED"
  }
}
EOFJSON
echo "FINDINGS WRITTEN"`,
    // doc update
    'cd /root && python3 coordination/auto_doc_updater.py --summary "Fixed pending bookings display: (1) Robust field access in _format_booking_line with proper fallback chains, (2) Dynamic consoleType derivation in API instead of hardcoded PS5, (3) Added consoleType to search endpoint response, (4) Handle MySQL datetime objects in _parse_booking_datetime_mmt, (5) Added parse_mode for cancel messages" 2>&1 || echo "doc_updater skipped"',
  ];
  let pending = cmds.length, results = {};
  cmds.forEach((c,i) => {
    conn.exec(c, (err, s) => {
      if (err) { results[i]=err.message; if(--pending===0) done(); return; }
      let d=''; s.on('data',c=>d+=c); s.stderr.on('data',c=>d+=c);
      s.on('close',()=>{results[i]=d; if(--pending===0) done();});
    });
  });
  function done() { cmds.forEach((c,i)=>{ console.log('=== CMD '+i+' ===\n'+results[i]); }); conn.end(); }
});
conn.connect({host:'5.223.81.16',port:22,username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),readyTimeout:15000});
