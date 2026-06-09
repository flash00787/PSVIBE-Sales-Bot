const { Client } = require('ssh2');
const fs = require('fs');

const host = '167.71.196.120';
const BOT_DIR = '/root/Sales-Tele-Bot_refactored';

function execCmd(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', d => stdout += d.toString());
      stream.stderr.on('data', d => stderr += d.toString());
      stream.on('close', code => resolve({ stdout: stdout.trim(), stderr: stderr.trim(), code }));
    });
  });
}

(async () => {
  const conn = new Client();
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve).on('error', reject);
    conn.connect({
      host, username: 'root',
      privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8')
    });
  });

  // Get states from app.py - format is STATE_NAME: not 'STATE_NAME':
  const r1 = await execCmd(conn, `cd ${BOT_DIR} && python3 -c "
with open('bot/app.py') as f:
    content = f.read()
# Find states dict
idx = content.find('states={')
if idx == -1:
    idx = content.find('states = {')
if idx == -1:
    idx = content.find('states=')
    if idx == -1: idx = content.find('states =')
    
# Find the opening brace
brace = content.find('{', idx)
if brace == -1:
    print('No brace found')
else:
    depth = 0
    for i in range(brace, len(content)):
        if content[i] == '{': depth += 1
        elif content[i] == '}': depth -= 1
        if depth == 0:
            chunk = content[brace:i+1]
            states = []
            for line in chunk.split(chunk):
                line = line.strip()
                if ':' in line and not line.startswith('#') and not line.startswith('{'):
                    key = line.split(':')[0].strip()
                    if key and not key.startswith(('MessageHandler','CommandHandler','CallbackQueryHandler','ConversationHandler')):
                        states.append(key)
            for s in sorted(set(states)):
                print(s)
            break
" 2>&1`);
  console.log('=== STATES FROM APP.PY (Python) ===');
  console.log(r1.stdout);
  if (r1.stderr) console.error('ERR:', r1.stderr);

  // Simpler approach: grep lines with handler assignments
  const r2 = await execCmd(conn, `cd ${BOT_DIR} && python3 -c "
with open('bot/app.py') as f:
    content = f.read()
import re
# Extract key names from the states dict - each line like 'STATE_NAME: [Handler...]'
states = set()
for m in re.finditer(r'^\\s+([A-Z][A-Z_0-9]+):', content, re.MULTILINE):
    # Filter out imports, class names, etc.
    key = m.group(1)
    if not any(key.startswith(x) for x in ['HTTP','TEL','Logger','Comman','Filter','Updat','DEFAU','Conv','Inte','Mess']):
        states.add(key)
for s in sorted(states):
    print(s)
" 2>&1`);
  console.log('\n=== STATES FROM APP.PY (regex) ===');
  console.log(r2.stdout);
  if (r2.stderr) console.error('ERR:', r2.stderr);

  conn.end();
})().catch(err => { console.error('FATAL:', err); process.exit(1); });
