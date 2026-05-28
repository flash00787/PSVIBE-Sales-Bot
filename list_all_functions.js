const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected - listing all functions');
  
  const pyScript = `
import ast

with open('/root/Personal-Wallet-Tele-Bot-2/bot/main.py', 'r') as f:
    tree = ast.parse(f.read())

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if 'error' in node.name.lower() or 'handler' in node.name.lower() or 'err' in node.name.lower() or 'app' in node.name.lower() or 'main' in node.name.lower():
            print(f"Line {node.lineno}: {type(node).__name__} {node.name}")
`;

  conn.exec(`python3 << 'PYEOF'\n${pyScript}\nPYEOF`, { pty: false }, (err, stream) => {
    if (err) {
      console.log('EXEC ERROR:', err);
      conn.end();
      return;
    }
    let output = '';
    stream.on('data', (data) => { output += data.toString(); });
    stream.stderr.on('data', (data) => { output += data.toString(); });
    stream.on('close', (code) => {
      console.log(output);
      conn.end();
    });
  });
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err);
  process.exit(1);
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
