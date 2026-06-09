const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  const cmd = `
echo "=== reports.py (first 80 lines) ==="
head -80 /root/psvibe-sales-bot/bot/handlers/reports.py
echo ""
echo "=== reports.py grep inventory ==="
grep -n -i 'inventory\|stock\|qty\|items\|data.get' /root/psvibe-sales-bot/bot/handlers/reports.py
echo ""
echo "=== sales.py grep food/stock/menu ==="
grep -n -i 'stock_map\|prompt_food_menu\|step_mins\|Food Menu\|food.*menu\|stock.*filter\|stock.*မရ' /root/psvibe-sales-bot/bot/handlers/sales.py
echo ""
echo "=== sales.py lines 740-800 ==="
sed -n '735,810p' /root/psvibe-sales-bot/bot/handlers/sales.py
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
