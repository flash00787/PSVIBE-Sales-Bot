const fs = require('fs');
const { Client } = require('ssh2');
const sshKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

const conn = new Client();

function run(cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let data = '';
      stream.on('data', (chunk) => { data += chunk; });
      stream.stderr.on('data', (chunk) => { process.stderr.write(chunk); });
      stream.on('close', () => resolve(data));
    });
  });
}

conn.on('ready', async () => {
  try {
    // Get all global _MBR_TS with context
    let r = await run('grep -n "global _MBR_TS" /root/psvibe-sales-bot/bot/__init__.py');
    console.log('=== global _MBR_TS ===');
    console.log(r);

    // Check if there's also a hidden duplicate in save_referral_code by looking at wider range with line numbers
    r = await run("awk 'NR>=2088 && NR<=2140 {printf \"%4d: %s\\n\", NR, $0}' /root/psvibe-sales-bot/bot/__init__.py");
    console.log('\n=== save_referral_code (2088-2140) ===');
    console.log(r);

    // _load_members function
    r = await run("awk 'NR>=1795 && NR<=1900 {printf \"%4d: %s\\n\", NR, $0}' /root/psvibe-sales-bot/bot/__init__.py");
    console.log('\n=== _load_members area (1795-1900) ===');
    console.log(r);

    // update_member_effective_rate function
    r = await run("awk 'NR>=2165 && NR<=2210 {printf \"%4d: %s\\n\", NR, $0}' /root/psvibe-sales-bot/bot/__init__.py");
    console.log('\n=== update_member_effective_rate (2165-2210) ===');
    console.log(r);

    conn.end();
  } catch(e) { console.error(e); conn.end(); }
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: sshKey
});
