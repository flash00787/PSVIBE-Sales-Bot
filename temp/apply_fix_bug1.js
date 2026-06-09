const {Client} = require('ssh2');
const fs = require('fs');
const conn = new Client();

conn.on('ready', () => {
  // Fix: add user feedback when wrong input at SALE_CONFIRM
  const cmd = `cd /root/psvibe-sales-bot && cp bot/handlers/sales.py bot/handlers/sales.py.bak.$(date +%s) && python3 -c "
import re
with open('bot/handlers/sales.py', 'r') as f:
    content = f.read()

# Fix Bug #1: Add user feedback before silent return SALE_CONFIRM
old = '''    if text != BTN_CONFIRM_SAVE:
        return SALE_CONFIRM'''

new = '''    if text != BTN_CONFIRM_SAVE:
        await update.message.reply_text(
            \\\"⚠️ \\\\\\\"Confirm & Save\\\\\\\" ခလုတ်ကိုသာ နှိပ်ပါ -\\\",
            reply_markup=ReplyKeyboardMarkup([[BTN_CONFIRM_SAVE], NAV_ROW], resize_keyboard=True),
        )
        return SALE_CONFIRM'''

if old in content:
    content = content.replace(old, new)
    with open('bot/handlers/sales.py', 'w') as f:
        f.write(content)
    print('FIXED: Bug #1 silent fail in step_sale_confirm')
else:
    print('NOT FOUND: old pattern not matched')
    # Show surrounding lines for debugging
    idx = content.find('if text != BTN_CONFIRM_SAVE')
    if idx >= 0:
        print('Found at:', idx)
        print(content[idx:idx+200])
"
python3 -c "import py_compile; py_compile.compile('bot/handlers/sales.py', doraise=True); print('COMPILE OK')"
systemctl restart psvibe-sale-bot
echo "RESTARTED"
sleep 2
systemctl is-active psvibe-sale-bot`;

  conn.exec(cmd, (err, stream) => {
    if(err) { console.log('ERR:', err); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => { console.log(out); conn.end(); });
  });
});
conn.connect({host:'5.223.81.16', username:'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')});
