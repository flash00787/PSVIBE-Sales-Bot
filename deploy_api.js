const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

conn.on('ready', () => {
  console.log('SSH CONNECTED');
  
  // Check Python, install deps, start server
  const cmd = `
    cd /root/psvibe_api_server &&
    echo "=== Python ===" &&
    python3 --version &&
    echo "=== pip ===" &&
    pip3 --version &&
    echo "=== Installing deps ===" &&
    pip3 install -r requirements.txt 2>&1 | tail -5 &&
    echo "=== Installing gspread ===" &&
    pip3 install gspread google-auth 2>&1 | tail -5 &&
    echo "=== Done installing ==="
  `;
  
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC ERROR:', err); conn.end(); return; }
    let data = ''; let stderrData = '';
    stream.on('data', (chunk) => { data += chunk.toString(); });
    stream.stderr.on('data', (chunk) => { stderrData += chunk.toString(); });
    stream.on('close', (code) => {
      console.log('EXIT:', code);
      console.log('STDOUT:', data.substring(0, 3000));
      if (stderrData) console.error('STDERR:', stderrData.substring(0, 1000));
      conn.end();
    });
  });
});
conn.on('error', (err) => { console.error('CONN ERROR:', err); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: key });
