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

async function main() {
  const conn = new Client();
  
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({ host: HOST, username: USER, privateKey: KEY });
  });

  console.log('=== CONNECTED ===');

  // Get V1 in chunks
  for (let start = 1; start <= 5831; start += 500) {
    const end = start + 499;
    const { stdout } = await execCommand(conn, `sed -n '${start},${end}p' /root/psvibe_sales_bot/customer_bot_original.py`);
    console.log(`\n\n===== V1 LINES ${start}-${end} =====`);
    console.log(stdout);
  }

  // Also check if there's a booking.py file in V2
  const booking = await execCommand(conn, 'cat /root/psvibe_sales_bot/customer_bot/booking.py 2>/dev/null || echo "NO booking.py"');
  console.log('\n\n===== V2 booking.py =====');
  console.log(booking.stdout);

  // Check data files
  const dataInit = await execCommand(conn, 'cat /root/psvibe_sales_bot/customer_bot/data/__init__.py');
  console.log('\n\n===== V2 data/__init__.py =====');
  console.log(dataInit.stdout);

  conn.end();
}

main().catch(err => { console.error('ERROR:', err); process.exit(1); });
