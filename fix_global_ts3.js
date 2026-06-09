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
      stream.stderr.on('data', (chunk) => { process.stderr.write('STDERR: ' + chunk); });
      stream.on('close', (code) => resolve({ data, code }));
    });
  });
}

conn.on('ready', async () => {
  try {
    // Fix: Move global _MBR_TS from inside try block to top of update_member_effective_rate
    // Remove the inner global and add it after the docstring
    
    // Step 1: Remove the inner global _MBR_TS at line 2176
    console.log('=== Step 1: Remove inner global at line 2176 ===');
    let r = await run(`sed -i '2176s/.*global _MBR_TS.*//' /root/psvibe-sales-bot/bot/__init__.py`);
    console.log('Remove result:', r.code);

    // Step 2: Add global _MBR_TS after the docstring (after line 2169)
    console.log('=== Step 2: Add global _MBR_TS after docstring ===');
    r = await run(`sed -i '2169a\\    global _MBR_TS' /root/psvibe-sales-bot/bot/__init__.py`);
    console.log('Add result:', r.code);

    // Verify the result
    console.log('\n=== VERIFICATION: update_member_effective_rate ===');
    r = await run(`awk 'NR>=2166 && NR<=2185 {printf "%4d: %s\\n", NR, $0}' /root/psvibe-sales-bot/bot/__init__.py`);
    console.log(r.data);

    // Also verify save_referral_code is still correct
    console.log('=== VERIFICATION: save_referral_code ===');
    r = await run(`awk 'NR>=2108 && NR<=2132 {printf "%4d: %s\\n", NR, $0}' /root/psvibe-sales-bot/bot/__init__.py`);
    console.log(r.data);

    // Check all global _MBR_TS
    console.log('=== All global _MBR_TS occurrences ===');
    r = await run(`grep -n 'global _MBR_TS' /root/psvibe-sales-bot/bot/__init__.py`);
    console.log(r.data);

    conn.end();
  } catch(e) { console.error(e); conn.end(); }
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: sshKey
});
