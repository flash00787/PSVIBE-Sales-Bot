const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  const cmd = `
echo "=== step_mins continued 740-790 ==="
sed -n '740,790p' /root/psvibe-sales-bot/bot/handlers/sales.py
echo ""
echo "=== find prompt_food_menu function ==="
grep -n 'async def prompt_food_menu' /root/psvibe-sales-bot/bot/handlers/sales.py
grep -n 'async def prompt_mins' /root/psvibe-sales-bot/bot/handlers/sales.py
echo ""
echo "=== search for food_menu related functions ==="
grep -n 'prompt_food\|food_menu\|Food Menu\|food_prices\|stock_map\|food.*filter\|stock.*မရ\|မရနိုင်' /root/psvibe-sales-bot/bot/handlers/sales.py
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
