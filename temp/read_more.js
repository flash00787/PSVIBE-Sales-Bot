const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  const cmd = `
echo "=== search for error messages in sales.py ==="
grep -n 'Food Menu.*မရ\|stock data.*မဆွဲ\|no food\|food_prices.*empty\|stock_map.*empty\|Stock.*In\|Stock_In' /root/psvibe-sales-bot/bot/handlers/sales.py
echo ""
echo "=== prompt_food_menu function ==="
grep -n 'prompt_food_menu\|async def prompt_food\|await prompt_food' /root/psvibe-sales-bot/bot/handlers/sales.py
echo ""
echo "=== step_mins function (full) ==="
grep -n 'async def step_mins\|async def prompt_mins\|async def prompt_food\|stock_map\|food_prices' /root/psvibe-sales-bot/bot/handlers/sales.py
echo ""
echo "=== lines around 620-740 for prompt_food_menu ==="
sed -n '620,740p' /root/psvibe-sales-bot/bot/handlers/sales.py
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
