const {Client} = require('ssh2');
const fs = require('fs');
const conn = new Client();

conn.on('ready', () => {
  // Kill existing bots, start fresh with API_BASE_URL env var
  const cmd = `
pkill -f "python3 main.py" 2>/dev/null
pkill -f "python3 customer_bot.py" 2>/dev/null
sleep 2

cd "/root/Aung Chan Myint/Sales-Tele-Bot"

API_BASE_URL=http://localhost:3000 nohup .venv/bin/python3 main.py >> main.log 2>&1 &
echo "MAIN_PID=$!"

API_BASE_URL=http://localhost:3000 nohup .venv/bin/python3 customer_bot.py >> customer.log 2>&1 &
echo "CUST_PID=$!"

sleep 5
echo "---CHECK---"
ps aux | grep "python3" | grep -v grep
echo "---CUST_LOG---"
tail -5 customer.log
echo "---MAIN_LOG---"
tail -5 main.log
`;
  
  conn.exec(cmd, (err, stream) => {
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => {
      console.log(out);
      conn.end();
    });
  });
});

conn.connect({
  host: '5.223.81.16',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
