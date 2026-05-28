const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

function execCommand(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', (data) => { stdout += data.toString(); });
      stream.stderr.on('data', (data) => { stderr += data.toString(); });
      stream.on('close', (code) => {
        resolve({ code, stdout: stdout.trim(), stderr: stderr.trim() });
      });
    });
  });
}

async function readFile(conn, path) {
  const { stdout } = await execCommand(conn, `cat "${path}" 2>/dev/null || echo "FILE_NOT_FOUND"`);
  return stdout;
}

async function main() {
  const conn = new Client();
  
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({ host: HOST, username: USER, privateKey: KEY });
  });

  console.log('=== CONNECTED ===');

  // List directory
  const { stdout: dirList } = await execCommand(conn, 'ls -la /root/psvibe_sales_bot/');
  console.log('ROOT DIR:\n', dirList);

  const { stdout: botDir } = await execCommand(conn, 'ls -la /root/psvibe_sales_bot/customer_bot/');
  console.log('CUSTOMER_BOT DIR:\n', botDir);

  const { stdout: dataDir } = await execCommand(conn, 'ls -la /root/psvibe_sales_bot/customer_bot/data/ 2>/dev/null || echo "no data dir"');
  console.log('DATA DIR:\n', dataDir);

  // Read all V2 files
  const files = [
    '/root/psvibe_sales_bot/customer_bot/__init__.py',
    '/root/psvibe_sales_bot/customer_bot/main.py',
    '/root/psvibe_sales_bot/customer_bot/handlers.py',
    '/root/psvibe_sales_bot/customer_bot/api.py',
    '/root/psvibe_sales_bot/customer_bot/ai.py',
  ];

  for (const f of files) {
    const content = await readFile(conn, f);
    console.log(`\n\n========== ${f} ==========`);
    console.log(content);
  }

  // Also read V1 file (first 200 lines to understand structure)
  const v1First = await execCommand(conn, 'head -200 /root/psvibe_sales_bot/customer_bot_original.py');
  console.log('\n\n========== V1 FIRST 200 LINES ==========');
  console.log(v1First.stdout);

  // Get V1 size and line count
  const v1Stats = await execCommand(conn, 'wc -l /root/psvibe_sales_bot/customer_bot_original.py');
  console.log('\nV1 LINE COUNT:', v1Stats.stdout);

  // Check the main bot file too
  const mainBot = await readFile(conn, '/root/psvibe_sales_bot/main.py');
  console.log('\n\n========== /root/psvibe_sales_bot/main.py ==========');
  console.log(mainBot);

  conn.end();
}

main().catch(err => { console.error('ERROR:', err); process.exit(1); });
