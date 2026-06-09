const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  // Fix _v1_compat.py - add missing aliases at the end
  // Also fix the handlers.py references and main.py imports
  conn.exec(`cat >> /root/psvibe_sales_bot/customer_bot/_v1_compat.py << 'ALIASES_EOF'

# ── V2 compatibility aliases ──────────────────────────────────────────────────
# These match the names that customer_bot/main.py and customer_bot/__init__.py expect
start = cmd_start
refresh_cmd = cmd_refresh
menu_cmd = cmd_menu
today_cmd = cmd_today
rate_cmd = cmd_rate
myid_cmd = cmd_myid
contact_cmd = cmd_contact
promotions_cmd = cmd_promotions
feedback_cmd = cmd_feedback
handle_free_text = handle_menu_buttons
bk_start = cmd_book
bk_end = cmd_cancel
bk_member_check = step_bk_member_check
bk_member_select = step_bk_member_select
bk_phone_verify = step_bk_phone_verify
bk_data_confirm = step_bk_data_confirm
bk_name = step_bk_name
bk_phone = step_bk_phone
bk_date = step_bk_date
bk_time = step_bk_time
bk_console = step_bk_console
bk_duration = step_bk_duration
bk_game = step_bk_game
bk_console_pref = step_bk_console_pref
bk_confirm = step_bk_confirm
bk_disc_warn = step_bk_disc_warn

# Also alias the conversation states (V2 main.py uses CBQH patterns, V1 uses MSGH)
# but main.py references the states for pattern matching which uses orig.BK_*
BK_END = ConversationHandler.END
ALIASES_EOF
echo "Aliases appended to _v1_compat.py"`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => {
      console.log(out);
      // Now fix main.py - use V1-style MessageHandlers not CallbackQueryHandlers for booking steps
      // Actually V2's main.py uses CallbackQueryHandler patterns that don't match V1's text-based approach
      // The simplest fix: rewrite main.py to replicate V1's original main() function structure
      // using MessageHandlers for booking steps (matching V1's actual handler types)
      
      // Actually, let me just check if it works now after adding aliases
      conn.exec('cd /root/psvibe_sales_bot && /root/venv/bin/python3 -c "import sys; sys.path.insert(0, chr(46)); from customer_bot import *; print(chr(86)+chr(50)+chr(32)+chr(105)+chr(109)+chr(112)+chr(111)+chr(114)+chr(116)+chr(32)+chr(79)+chr(75))" 2>&1', (err2, stream2) => {
        let out2 = '';
        stream2.on('data', d => out2 += d.toString());
        stream2.stderr.on('data', d => out2 += d.toString());
        stream2.on('close', () => {
          console.log('Import test:', out2);
          conn.end();
        });
      });
    });
  });
});
conn.connect({ host: '5.223.81.16', username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8') });
