const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();
const OUTPUT_FILE = '/home/node/.openclaw/workspace/temp/fix_food_inventory.txt';

function log(msg) {
    fs.appendFileSync(OUTPUT_FILE, msg + '\n');
    console.log(msg);
}

function runCmd(cmd, label) {
    return new Promise((resolve, reject) => {
        log(`\n--- ${label} ---`);
        log(`$ ${cmd}`);
        conn.exec(cmd, (err, stream) => {
            if (err) { log(`ERROR: ${err.message}`); resolve(''); return; }
            let out = '';
            stream.on('close', (code) => {
                log(`[exit: ${code}]`);
                resolve(out);
            });
            stream.on('data', (data) => { out += data.toString(); });
            stream.stderr.on('data', (data) => { out += data.toString(); });
        });
    }).then(result => {
        log(result);
        return result;
    });
}

conn.on('ready', async () => {
    log('\n=== DEEP DIVE INVESTIGATION ===\n');

    // BUG 1: Sales Daily tab - food menu stock filter
    // Look at prompt_food_menu in sales.py
    await runCmd(
        'grep -n "prompt_food_menu\\|stock_map\\|food_stock_map\\|stock_filter\\|Stock" /root/psvibe-sales-bot/bot/handlers/sales.py | head -60',
        'BUG1-A: sales.py stock/food references'
    );

    // Look at the full prompt_food_menu function
    await runCmd(
        'python3 -c "
import ast, sys
with open(\"/root/psvibe-sales-bot/bot/handlers/sales.py\") as f:
    lines = f.readlines()
    for i, line in enumerate(lines, 1):
        if \"prompt_food_menu\" in line or \"step_food_menu\" in line or \"food_stock_map\" in line or \"stock_map\" in line:
            print(f\"{i}: {line.rstrip()}\")
"',
        'BUG1-B: Relevant lines in sales.py'
    );

    // Look at the full prompt_food_menu function body
    await runCmd(
        'python3 -c "
with open(\"/root/psvibe-sales-bot/bot/handlers/sales.py\") as f:
    lines = f.readlines()
    in_func = False
    for i, line in enumerate(lines, 1):
        if \"async def prompt_food_menu\" in line:
            in_func = True
        if in_func:
            print(f\"{i}: {line.rstrip()}\")
            if in_func and line.strip() == \"\" and i > 1:
                # check if next non-empty is another function
                pass
        if in_func and \"async def \" in line and \"prompt_food_menu\" not in line:
            break
"',
        'BUG1-C: prompt_food_menu function'
    );

    // BUG 2: Inventory button - cmd_inventory in reports.py
    await runCmd(
        'python3 -c "
with open(\"/root/psvibe-sales-bot/bot/handlers/reports.py\") as f:
    lines = f.readlines()
    in_func = False
    for i, line in enumerate(lines, 1):
        if \"async def cmd_inventory\" in line:
            in_func = True
        if in_func:
            print(f\"{i}: {line.rstrip()}\")
        if in_func and \"async def cmd_\" in line and \"cmd_inventory\" not in line:
            in_func = False
"',
        'BUG2-A: cmd_inventory function'
    );

    // Check the API client for inventory endpoint
    await runCmd(
        'grep -n "inventory\\|Inventory" /root/psvibe-sales-bot/bot/api_client.py',
        'BUG2-B: api_client inventory references'
    );

    // Check the _replit_get function
    await runCmd(
        'grep -n "_replit_get\\|_replit_post\\|def _replit" /root/psvibe-sales-bot/bot/handlers/reports.py | head -10',
        'BUG2-C: _replit_get in reports.py'
    );

    // Check bot/__init__.py for sheet setup and inventory
    await runCmd(
        'grep -n "inv_sh\\|Inventory\\|inventory\\|inv_ws\\|worksheet.*inv\\|sheet.*inv" /root/psvibe-sales-bot/bot/__init__.py | head -20',
        'BUG2-D: bot/__init__.py inventory setup'
    );

    // Check the actual environment SHEET_ID
    await runCmd(
        'grep SHEET_ID /root/psvibe-sales-bot/.env 2>/dev/null; grep SHEET_ID /root/psvibe_api_server/.env 2>/dev/null; echo "==="; systemctl show psvibe-sale-bot --property=Environment 2>/dev/null; echo "==="; systemctl cat psvibe-sale-bot 2>/dev/null | head -40',
        'ENV: SHEET_ID from env and systemd'
    );

    // Check API server for Sales Daily endpoint
    await runCmd(
        'grep -n "sales.daily\\|sales_daily\\|get_sales_daily\\|Sales Daily" /root/psvibe_api_server/patch_routes.py | head -30',
        'API: Sales Daily endpoint in patch_routes.py'
    );

    // Check API server inventory endpoint
    await runCmd(
        'grep -n "inventory\\|Inventory" /root/psvibe_api_server/patch_routes.py | head -20',
        'API: Inventory endpoint in patch_routes.py'
    );

    // Check sheets_client.py
    await runCmd(
        'cat /root/psvibe_api_server/sheets_client.py',
        'API: sheets_client.py full'
    );

    // Check bot/__init__.py lazy worksheet
    await runCmd(
        'python3 -c "
with open(\"/root/psvibe-sales-bot/bot/__init__.py\") as f:
    lines = f.readlines()
    in_ws = False
    for i, line in enumerate(lines, 1):
        if \"inv_sh\" in line or (in_ws and \"_LazyWorksheet\" in line):
            in_ws = True
        if in_ws:
            print(f\"{i}: {line.rstrip()}\")
            if line.strip() == \"\" and in_ws:
                break
"',
        'BOT: _LazyWorksheet and inv_sh'
    );

    log('\n=== DEEP DIVE COMPLETE ===');
    conn.end();
});

conn.on('error', (err) => {
    fs.appendFileSync(OUTPUT_FILE, `SSH ERROR: ${err.message}\n`);
    console.error('SSH ERROR:', err.message);
    process.exit(1);
});

conn.connect({
    host: '5.223.81.16',
    port: 22,
    username: 'root',
    privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
