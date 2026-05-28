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

// Extract booking-related lines from V1 (lines 2500-5050)
async function main() {
  const conn = new Client();
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve); conn.on('error', reject);
    conn.connect({ host: HOST, username: USER, privateKey: KEY });
  });

  // Step 1: Create backups directory
  await execCommand(conn, 'mkdir -p /root/backups');
  console.log('Backups dir created');

  // Step 2: Backup V1
  await execCommand(conn, 'cp /root/psvibe_sales_bot/customer_bot_original.py /root/backups/customer_bot_original.py.$(date +%Y%m%d_%H%M%S)');
  console.log('V1 backed up');

  // Step 3: Create booking.py - extract V1 booking code and adapt it
  // Read V1 lines 886-960 (button labels, constants)  
  const { stdout: v1_lines_886_960 } = await execCommand(conn, "sed -n '886,960p' /root/psvibe_sales_bot/customer_bot_original.py");
  console.log('Got V1 886-960');

  // Step 4: Check what data files exist
  const { stdout: dataFiles } = await execCommand(conn, 'ls -la /root/psvibe_sales_bot/customer_bot/data/');
  console.log('Data files:\n', dataFiles);

  // Step 5: Check if booking.py needs any V1 utility functions
  // Read the _split_message from V1 (line 1020-1036)
  const { stdout: splitMsg } = await execCommand(conn, "sed -n '1020,1036p' /root/psvibe_sales_bot/customer_bot_original.py");
  console.log('Split message:\n', splitMsg);

  conn.end();
}
main().catch(e => { console.error(e); process.exit(1); });
