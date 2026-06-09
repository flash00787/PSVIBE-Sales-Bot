const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

function runCmd(cmd, timeout = 15000) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, { timeout }, (err, stream) => {
      if (err) return reject(err);
      let out = '', errOut = '';
      stream.on('data', (d) => { out += d.toString(); });
      stream.stderr.on('data', (d) => { errOut += d.toString(); });
      stream.on('close', (code) => resolve({ code, stdout: out.trim(), stderr: errOut.trim() }));
    });
  });
}

async function main() {
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: KEY });
  });
  console.log('=== CONNECTED ===\n');

  // Check all psvibe-related services
  console.log('--- ALL PSVIBE SERVICES ---');
  let r = await runCmd('systemctl list-units --type=service --all | grep -i psvibe');
  console.log(r.stdout);
  console.log('');

  // Check specifically for conflicting services using same tokens
  console.log('--- SERVICE DETAILS FOR BOT-TOKEN SERVICES ---');
  r = await runCmd(`
    echo "=== psvibe-sale-bot ===" 
    systemctl show psvibe-sale-bot 2>/dev/null | grep -E "ActiveState|SubState|EnvironmentFiles|ExecStart"
    echo ""
    echo "=== psvibe_sales_bot ===" 
    systemctl show psvibe_sales_bot 2>/dev/null | grep -E "ActiveState|SubState|EnvironmentFiles|ExecStart"
    echo ""
    echo "=== psvibe_customer_bot ===" 
    systemctl show psvibe_customer_bot 2>/dev/null | grep -E "ActiveState|SubState|EnvironmentFiles|ExecStart"
    echo ""
    echo "=== psvibe-customer ===" 
    systemctl show psvibe-customer 2>/dev/null | grep -E "ActiveState|SubState|EnvironmentFiles|ExecStart"
    echo ""
    echo "=== psvibe-api-server ===" 
    systemctl show psvibe-api-server 2>/dev/null | grep -E "ActiveState|SubState|EnvironmentFiles|ExecStart"
    echo ""
    echo "=== psvibe-api ===" 
    systemctl show psvibe-api 2>/dev/null | grep -E "ActiveState|SubState|EnvironmentFiles|ExecStart"
  `);
  console.log(r.stdout);
  console.log('');

  // Check journal for 409 errors
  console.log('--- RECENT 409 CONFLICT ERRORS ---');
  r = await runCmd('journalctl -u psvibe-sale-bot -u psvibe_customer_bot -u psvibe-customer --since "2 hours ago" 2>/dev/null | grep -i "409\\|conflict\\|terminated by other" | tail -20');
  console.log(r.stdout || '(none found)');
  console.log('');

  // Check /root/.env vs /etc/psvibe/secrets.env for conflicting exports
  console.log('--- POTENTIAL CONFLICT: /root/.env vs /etc/psvibe/secrets.env ---');
  r = await runCmd(`
    echo "=== /root/.env BOT_TOKEN ===" 
    grep "^BOT_TOKEN=" /root/.env 2>/dev/null
    echo ""
    echo "=== /etc/psvibe/secrets.env BOT_TOKEN ===" 
    grep "^BOT_TOKEN=" /etc/psvibe/secrets.env 2>/dev/null
    echo ""
    echo "=== DIFF (if any) ===" 
    diff <(grep "^BOT_TOKEN=" /root/.env 2>/dev/null) <(grep "^BOT_TOKEN=" /etc/psvibe/secrets.env 2>/dev/null) || echo "SAME"
  `);
  console.log(r.stdout);

  console.log('\n=== AUDIT COMPLETE ===');
  conn.end();
}

main().catch(e => { console.error('ERROR:', e); conn.end(); process.exit(1); });
