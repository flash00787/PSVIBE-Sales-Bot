const { Client } = require('ssh2');

const conn = new Client();
const commands = [
  // Check app.py for how it handles allowed IDs
  'grep -n "allowed\\|ALLOWED\\|staff\\|user.*id\\|chat.*id\\|B30\\|setting\\|Setting\\|fetch.*config\\|config.*setting" /root/psvibe-sale-bot/bot/app.py 2>/dev/null | head -30',
  // Check main.py for show_main_menu or auth
  'grep -n "def show_main_menu\\|main_menu\\|start\\|auth\\|allow\\|user.*id\\|B30" /root/psvibe-sale-bot/main.py 2>/dev/null | head -20',
  // Check API server for settings/config endpoint
  'grep -rn "config\\|setting\\|allowed\\|B30" /root/psvibe_api_server/app.py 2>/dev/null | head -20',
  // Check if API server is running and healthy
  'curl -s http://localhost:8000/api/sheets/config 2>/dev/null | head -5',
  // Check the settings endpoint - there might be a different path
  'curl -s http://localhost:8000/api/sheets/settings 2>/dev/null | head -5',
  // Check API key
  'grep -rn "API_KEY\\|api_key\\|api-key" /root/psvibe_api_server/app.py 2>/dev/null | head -10',
  // Check what routes the API server has  
  'grep -n "router\\|route\\|@app\\|add_api\\|include_router\\|def.*get" /root/psvibe_api_server/app.py 2>/dev/null | head -30',
];

conn.on('ready', () => {
  let results = [];
  let idx = 0;

  function runNext() {
    if (idx >= commands.length) {
      console.log(JSON.stringify(results, null, 2));
      conn.end();
      return;
    }
    const cmd = commands[idx];
    conn.exec(cmd, (err, stream) => {
      let stdout = '', stderr = '';
      if (err) {
        results.push({ cmd, error: err.message, stdout: '', stderr: '' });
        idx++; runNext();
        return;
      }
      stream.on('data', (d) => stdout += d.toString());
      stream.stderr.on('data', (d) => stderr += d.toString());
      stream.on('close', () => {
        results.push({ cmd, stdout: stdout.trim(), stderr: stderr.trim() });
        idx++; runNext();
      });
    });
  }
  runNext();
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: require('fs').readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
