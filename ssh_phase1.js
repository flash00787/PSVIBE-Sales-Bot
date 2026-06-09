const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const FILE = '/root/psvibe-sales-bot/bot/__init__.py';

function sshExec(cmd) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { conn.end(); reject(err); return; }
        let stdout = '', stderr = '';
        stream.on('data', (d) => stdout += d);
        stream.stderr.on('data', (d) => stderr += d);
        stream.on('close', (code) => {
          conn.end();
          resolve({ code, stdout, stderr });
        });
      });
    }).on('error', reject).connect({
      host: HOST, username: USER,
      privateKey: fs.readFileSync(KEY)
    });
  });
}

async function main() {
  // Step A: Backup first
  console.log('=== Step A: Backup ===');
  let r = await sshExec(`cp ${FILE} ${FILE}.bak`);
  console.log(`Backup: exit=${r.code} | ${r.stderr ? r.stderr : 'ok'}`);

  // Read current file to understand structure
  console.log('=== Reading file structure ===');
  r = await sshExec(`sed -n '1,25p' ${FILE}`);
  console.log('Lines 1-25:', r.stdout);

  r = await sshExec(`awk 'NR>=200 && NR<=235' ${FILE}`);
  console.log('Lines 200-235:', r.stdout);

  // Check for scope/credentials block
  r = await sshExec(`grep -n 'scope\\|creds\\|Credentials\\|SERVICE_ACCOUNT\\|service_account' ${FILE} | head -5`);
  console.log('Scope/creds lines:', r.stdout);

  // Check where gc and wb are defined
  r = await sshExec(`grep -n '^gc \\|^wb \\|[.]authorize\\|gspread\\.authorize\\|sheets_client\\|gc =' ${FILE} | head -5`);
  console.log('gc/wb definition lines:', r.stdout);
}

main().catch(console.error);
