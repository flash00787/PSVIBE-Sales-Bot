const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = path.join(process.env.HOME, '.openclaw/workspace/.ssh/id_rsa');
const NEW_PASS = 'PsVibe@2026_Rotated!';

function sshExec(conn, cmd, timeout = 15000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      stream?.close?.();
      resolve({ code: -1, stdout: '', stderr: 'TIMEOUT' });
    }, timeout);
    
    let stream;
    conn.exec(cmd, (err, s) => {
      if (err) { clearTimeout(timer); return reject(err); }
      stream = s;
      let stdout = '';
      let stderr = '';
      s.on('data', (data) => { stdout += data.toString(); });
      s.stderr.on('data', (data) => { stderr += data.toString(); });
      s.on('close', (code) => {
        clearTimeout(timer);
        resolve({ code, stdout, stderr });
      });
    });
  });
}

async function main() {
  const conn = new Client();
  
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({
      host: HOST,
      port: 22,
      username: USER,
      privateKey: fs.readFileSync(KEY_PATH),
    });
  });
  
  console.log('✅ Connected to VPS');

  // Step 6: Restart the correct API service
  console.log('\n--- Step 6a: Check which psvibe-api service to restart ---');
  let r6a = await sshExec(conn, "systemctl list-units --type=service | grep psvibe-api");
  console.log('API services:', r6a.stdout.trim());
  
  // Restart psvibe-api.service (the running one)
  console.log('\n--- Step 6b: Restart psvibe-api.service ---');
  let r6b = await sshExec(conn, "systemctl restart psvibe-api.service 2>&1", 20000);
  console.log('restart stdout:', r6b.stdout || '(empty)');
  console.log('restart stderr:', r6b.stderr || '(none)');
  console.log('exit code:', r6b.code);
  
  // Check status
  await new Promise(r => setTimeout(r, 3000));
  let r6c = await sshExec(conn, "systemctl status psvibe-api.service --no-pager -l 2>&1 | head -20");
  console.log('\nStatus after restart:');
  console.log(r6c.stdout);

  // Step 7: Verify new password
  console.log('\n--- Step 7: Verify new password ---');
  let r7 = await sshExec(conn, `docker exec psvibe-mysql mysql -upsvibe_user -p'${NEW_PASS}' -e "SHOW DATABASES;" 2>&1`);
  console.log('Verification stdout:', r7.stdout || '(empty)');
  console.log('Verification stderr:', r7.stderr || '(none)');
  console.log('Verification exit code:', r7.code);

  // Also verify secrets file is still correct
  console.log('\n--- Verify secrets.env ---');
  let r8 = await sshExec(conn, "grep MYSQL_PASSWORD /etc/psvibe/secrets.env");
  console.log('Secrets MYSQL line:', r8.stdout.trim());

  conn.end();
  console.log('\n✅ Complete');
}

main().catch(err => {
  console.error('❌ Error:', err.message);
  process.exit(1);
});
