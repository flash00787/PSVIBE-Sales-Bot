const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();
const OUTPUT_FILE = '/home/node/.openclaw/workspace/temp/fix_food_inventory.txt';

function log(msg) {
    fs.appendFileSync(OUTPUT_FILE, msg + '\n');
    console.log(msg);
}

fs.writeFileSync(OUTPUT_FILE, '=== PS VIBE BUG INVESTIGATION ===\n' + new Date().toISOString() + '\n\n');

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
    log('SSH connected successfully\n');

    // Step 2: Find Google Sheet ID
    let out1 = await runCmd(
        'grep -r "spreadsheet\\|SPREADSHEET\\|SHEET_ID\\|sheet_id" /root/psvibe_api_server/ --include="*.py" | head -30',
        'STEP 2a: Find Sheet ID references in api_server'
    );

    let out2 = await runCmd(
        'cat /root/psvibe_api_server/config.py 2>/dev/null || echo "config.py not found"',
        'STEP 2b: Read config.py'
    );

    // Check for .env or environment files
    let out3 = await runCmd(
        'ls -la /root/psvibe_api_server/*.env /root/psvibe_api_server/*.json /root/psvibe_api_server/*.yaml 2>/dev/null; cat /root/psvibe_api_server/.env 2>/dev/null | head -30',
        'STEP 2c: Environment files'
    );

    // Step 3: Check Sales Daily references
    let out4 = await runCmd(
        'grep -r "Sales Daily\\|sales.daily\\|sales_daily\\|SALES_DAILY\\|food\\|Food\\|inventory\\|Inventory\\|INVENTORY" /root/psvibe_api_server/ --include="*.py" -l',
        'STEP 3a: Files mentioning Sales Daily/Inventory/food'
    );

    let out5 = await runCmd(
        'grep -r "Sales Daily\\|sales.daily\\|sales_daily\\|SALES_DAILY\\|food\\|Food\\|inventory\\|Inventory\\|INVENTORY" /root/psvibe_api_server/ --include="*.py" | head -60',
        'STEP 3b: Context lines for Sales Daily/Inventory/food'
    );

    // Step 4: Check sales bot for Inventory button handling
    let out6 = await runCmd(
        'grep -r "Inventory\\|inventory\\|food_menu\\|food stock\\|stock\\|filter" /root/psvibe-sales-bot/ --include="*.py" -l | head -30',
        'STEP 4a: Sales bot files mentioning Inventory/filter/stock'
    );

    let out7 = await runCmd(
        'grep -r "Inventory\\|inventory\\|food_menu\\|stock_food\\|food_stock\\|FoodFilter\\|food_filter" /root/psvibe-sales-bot/ --include="*.py" | head -80',
        'STEP 4b: Sales bot Inventory/stock context'
    );

    // Step 6: git logs
    await runCmd('cd /root/psvibe_api_server && git log --oneline -15', 'STEP 6: api_server git log');
    await runCmd('cd /root/psvibe-sales-bot && git log --oneline -15', 'STEP 7: sales-bot git log');

    // Check for gspread/SQL references
    await runCmd(
        'grep -r "gspread\\|gspread" /root/psvibe_api_server/ --include="*.py" -l 2>/dev/null; echo "---"; grep -r "gspread\\|export.*sheet\\|to.*sheet\\|write.*sheet" /root/psvibe-sales-bot/ --include="*.py" -l 2>/dev/null | head -20',
        'STEP 8a: gspread references'
    );

    await runCmd(
        'grep -rn "SHEET\\|sheet\\|Sheet" /root/psvibe_api_server/config.py 2>/dev/null | head -30; echo "==="; grep -rn "SHEET\\|sheet\\|Sheet" /root/psvibe_api_server/app/ --include="*.py" -l 2>/dev/null | head -20',
        'STEP 8b: Sheet config in api_server'
    );

    // Also check the actual Google Sheet referenced
    await runCmd(
        'grep -rn "19zHR6\\|GOOGLE_SHEET\\|google_sheet\\|sheet_id\\|SPREADSHEET_ID" /root/psvibe-sales-bot/ --include="*.py" | head -20; echo "==="; grep -rn "19zHR6\\|GOOGLE_SHEET\\|google_sheet\\|sheet_id\\|SPREADSHEET_ID" /root/psvibe_api_server/ --include="*.py" | head -20',
        'STEP 8c: Specific Sheet ID references'
    );

    log('\n=== INVESTIGATION COMPLETE ===');
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
