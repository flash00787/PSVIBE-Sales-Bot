const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const privateKey = fs.readFileSync(KEY_PATH, 'utf8');

conn.on('ready', () => {
  const commands = `
    echo "=== FULL TREE ===";
    find /root/Sales-Tele-Bot_refactored/ -type f -name "*.py" -o -name "*.json" -o -name "*.md" -o -name "*.env" -o -name "*.txt" -o -name "*.yaml" -o -name "*.yml" -o -name "*.toml" | sort;
    echo "=== __init__.py content ===";
    cat /root/Sales-Tele-Bot_refactored/bot/__init__.py 2>/dev/null || echo "NO __init__.py";
    echo "=== Find all files containing receipt ===";
    grep -rl "receipt\|RECEIPT" /root/Sales-Tele-Bot_refactored/ 2>/dev/null || echo "NONE FOUND";
    echo "=== .env or config ===";
    cat /root/Sales-Tele-Bot_refactored/.env 2>/dev/null;
    cat /root/Sales-Tele-Bot_refactored/.env.example 2>/dev/null || echo "NO .env files";
    echo "=== bot directory listing ===";
    ls -la /root/Sales-Tele-Bot_refactored/bot/ 2>/dev/null || echo "NO bot dir";
    echo "=== root directory listing ===";
    ls -la /root/Sales-Tele-Bot_refactored/;
  `;
  
  conn.exec(commands, (err, stream) => {
    if (err) { console.error(err.message); process.exit(1); }
    let output = '';
    stream.on('data', d => output += d.toString());
    stream.stderr.on('data', d => output += d.toString());
    stream.on('close', () => {
      console.log(output);
      conn.end();
    });
  });
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey,
});
