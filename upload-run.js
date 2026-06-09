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
    conn.on('ready', resolve); conn.on('error', reject);
    conn.connect({ host: HOST, username: USER, privateKey: KEY });
  });

  // Upload deploy script
  const scriptContent = fs.readFileSync('/home/node/.openclaw/workspace/deploy-v2.py', 'utf8');
  
  // Write via base64
  const b64 = Buffer.from(scriptContent).toString('base64');
  await execCommand(conn, `echo '${b64}' | base64 -d > /root/deploy-v2.py`);
  console.log('Script uploaded');

  // Run it
  const result = await execCommand(conn, 'cd /root/psvibe_sales_bot && python3 /root/deploy-v2.py 2>&1');
  console.log('=== OUTPUT ===');
  console.log(result.stdout);
  if (result.stderr) console.log('=== STDERR ===\n' + result.stderr);
  console.log('=== EXIT CODE: ' + result.code + ' ===');

  conn.end();
}
main().catch(e => { console.error(e); process.exit(1); });
