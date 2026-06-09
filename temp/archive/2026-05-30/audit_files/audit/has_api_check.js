const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
let result = '';
conn.on('ready', () => {
  conn.exec(`grep -n '_HAS_API\|API_BASE_URL\|API_KEY' /root/psvibe-sale-bot/bot/__init__.py | head -30 && echo '---' && grep -n 'save_attendance.*api\|create_booking.*api\|end_booking.*api\|cancel_booking.*api\|add_console_game.*api\|remove_console_game.*api\|update_game_library_install.*api\|add_console_to_setting.*api\|remove_console_from_setting.*api\|set_game_disc_count.*api' /root/psvibe-sale-bot/bot/__init__.py && echo '---' && python3 -c "
import re
with open('/root/psvibe-sale-bot/bot/__init__.py') as f:
    content = f.read()

# Find _HAS_API definition and its impact
m = re.search(r'_HAS_API\\s*=\\s*(.+?)(?:\\n|$)', content)
if m:
    print('_HAS_API =', m.group(1)[:200])

# Find save_attendance function specifically  
start = content.find('def save_attendance(')
if start >= 0:
    snippet = content[start:start+800]
    print('\\nsave_attendance impl:')
    for line in snippet.split(chr(10))[:25]:
        print(line)
"`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    stream.on('data', (d) => { result += d.toString(); });
    stream.stderr.on('data', (d) => { result += d.toString(); });
    stream.on('close', () => { 
      console.log(result);
      conn.end(); 
    });
  });
});
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
