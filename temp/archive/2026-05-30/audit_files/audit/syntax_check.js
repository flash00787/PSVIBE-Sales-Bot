const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  const cmd = `python3 -c "
import ast, os
for f in sorted(os.listdir('/root/psvibe-sale-bot/bot/handlers')):
    if not f.endswith('.py'): continue
    try:
        ast.parse(open(os.path.join('/root/psvibe-sale-bot/bot/handlers', f)).read())
        print(f'OK: {f}')
    except SyntaxError as e:
        print(f'SYNTAX ERROR: {f} -> {e}')
"`;
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    let data = '';
    stream.on('data', chunk => data += chunk.toString());
    stream.on('close', () => {
      console.log(data);
      conn.end();
      process.exit(0);
    });
  });
}).connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
