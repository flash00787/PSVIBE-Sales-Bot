const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

async function execCommand(conn, cmd) {
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
    conn.on('ready', resolve); conn.on('error', reject);
    conn.connect({ host: HOST, username: USER, privateKey: KEY });
  });

  // Extract line numbers for key functions from V1
  const grep = await execCommand(conn, `grep -n '^async def \\|^def \\|^class \\|^# ──\\|^# ══' /root/psvibe_sales_bot/customer_bot_original.py`);
  console.log('=== KEY LINE NUMBERS ===');
  console.log(grep.stdout);

  conn.end();
}
main().catch(e => { console.error(e); process.exit(1); });
