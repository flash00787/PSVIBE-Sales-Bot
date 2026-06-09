const { Client } = require("ssh2");
const conn = new Client();
conn.on("ready", () => {
  conn.exec("echo '=== prompts.py ===' && python3 -c \"import ast; ast.parse(open('/root/psvibe-sale-bot/customer_bot/data/prompts.py').read()); print('OK')\" 2>&1 && echo '=== ai.py ===' && python3 -c \"import ast; ast.parse(open('/root/psvibe-sale-bot/customer_bot/ai.py').read()); print('OK')\" 2>&1 && echo '=== Verify async def ===' && grep -n '^async def _build_ai_system_prompt' /root/psvibe-sale-bot/customer_bot/data/prompts.py 2>/dev/null && echo '=== Verify await calls ===' && grep -n 'await fetch_config_fn\\|await build_rate_lines_fn\\|await build_bonus_table_fn\\|await fetch_games_full_fn' /root/psvibe-sale-bot/customer_bot/data/prompts.py 2>/dev/null && echo '=== Verify ai.py await ===' && grep -n 'await _build_ai_system_prompt' /root/psvibe-sale-bot/customer_bot/ai.py 2>/dev/null", (err, stream) => {
    let out = "";
    stream.on("data", (d) => (out += d));
    stream.on("close", () => { console.log(out); conn.end(); });
  });
});
conn.connect({
  host: "5.223.81.16", port: 22, username: "root",
  privateKey: require("fs").readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa"),
  readyTimeout: 5000
});
