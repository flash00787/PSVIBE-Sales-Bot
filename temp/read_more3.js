const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  const cmd = `
echo "=== prompt_food_menu (around line 203) ==="
sed -n '200,270p' /root/psvibe-sales-bot/bot/handlers/sales.py
echo ""
echo "=== prompt_mins (around line 111) ==="
sed -n '108,140p' /root/psvibe-sales-bot/bot/handlers/sales.py
`;
  
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC ERROR:', err); conn.end(); return; }
    let output = '';
    stream.on('data', (data) => { output += data.toString(); });
    stream.stderr.on('data', (data) => { console.error('STDERR:', data.toString()); });
    stream.on('close', (code, signal) => {
      console.log('=== OUTPUT ===');
      console.log(output);
      console.log('=== END ===');
      conn.end();
    });
  });
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: privateKey,
  readyTimeout: 15000,
});
