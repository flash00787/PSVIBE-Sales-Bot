const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = path.join(__dirname, '.ssh', 'id_rsa');

async function sshExec(command, timeout = 60000) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let output = '';
    let errOutput = '';
    let timer = setTimeout(() => {
      conn.end();
      reject(new Error(`Timeout after ${timeout}ms: ${command.substring(0,100)}`));
    }, timeout);

    conn.on('ready', () => {
      conn.exec(command, (err, stream) => {
        if (err) {
          clearTimeout(timer);
          conn.end();
          return reject(err);
        }
        stream.on('close', (code, signal) => {
          clearTimeout(timer);
          conn.end();
          resolve({ code, stdout: output, stderr: errOutput });
        }).on('data', (data) => { output += data.toString(); })
          .stderr.on('data', (data) => { errOutput += data.toString(); });
      });
    });

    conn.on('error', (err) => {
      clearTimeout(timer);
      reject(err);
    });

    conn.connect({
      host: HOST,
      port: 22,
      username: USER,
      privateKey: fs.readFileSync(KEY_PATH),
      readyTimeout: 15000,
    });
  });
}

async function runAll() {
  const commands = [
    {
      label: 'DESCRIBE sales_records',
      cmd: 'mysql -u root --database=psvibe -e "DESCRIBE sales_records;" 2>&1',
    },
    {
      label: 'SELECT sales_records LIMIT 3',
      cmd: 'mysql -u root --database=psvibe -e "SELECT * FROM sales_records LIMIT 3;" 2>&1',
    },
    {
      label: 'DESCRIBE opex_expenses',
      cmd: 'mysql -u root --database=psvibe_dashboard -e "DESCRIBE opex_expenses;" 2>&1',
    },
    {
      label: 'SELECT opex_expenses',
      cmd: 'mysql -u root --database=psvibe_dashboard -e "SELECT * FROM opex_expenses;" 2>&1',
    },
    {
      label: 'DESCRIBE income_by_acct',
      cmd: 'mysql -u root --database=psvibe_dashboard -e "DESCRIBE income_by_acct;" 2>&1',
    },
    {
      label: 'SELECT income_by_acct',
      cmd: 'mysql -u root --database=psvibe_dashboard -e "SELECT * FROM income_by_acct;" 2>&1',
    },
    {
      label: 'DESCRIBE cash_movements',
      cmd: 'mysql -u root --database=psvibe_dashboard -e "DESCRIBE cash_movements;" 2>&1',
    },
    {
      label: 'SELECT cash_movements',
      cmd: 'mysql -u root --database=psvibe_dashboard -e "SELECT * FROM cash_movements;" 2>&1',
    },
  ];

  const results = [];
  for (const { label, cmd } of commands) {
    console.log(`\n=== ${label} ===`);
    try {
      const r = await sshExec(cmd, 30000);
      console.log(`Exit: ${r.code}`);
      console.log(r.stdout);
      if (r.stderr) console.log('STDERR:', r.stderr);
    } catch (e) {
      console.log(`ERROR: ${e.message}`);
    }
  }

  // Also check the API endpoint
  console.log('\n\n=== API ENDPOINT ===');
  try {
    const r = await sshExec('grep -n -A 100 "def get_finance_balances" /root/psvibe_api_server/dashboard_routes.py', 30000);
    console.log(r.stdout);
    if (r.stderr) console.log('STDERR:', r.stderr);
  } catch (e) {
    console.log(`ERROR: ${e.message}`);
  }

  // Read the Vue file
  console.log('\n\n=== FINANCEBALANCE.VUE ===');
  try {
    const r = await sshExec('cat /root/psvibe-dashboard/src/views/FinanceBalance.vue', 30000);
    console.log(r.stdout);
    if (r.stderr) console.log('STDERR:', r.stderr);
  } catch (e) {
    console.log(`ERROR: ${e.message}`);
  }
}

runAll().catch(e => console.error('FATAL:', e));
