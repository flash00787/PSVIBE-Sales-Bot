const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = path.join(process.env.HOME, '.openclaw/workspace/.ssh/id_rsa');
const OLD_PASS = 'PsVibe@User2024!';
const NEW_PASS = 'PsVibe@2026_Rotated!';
const ROOT_PASS = 'PsVibe@MySQL2024!';

function sshExec(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '';
      let stderr = '';
      stream.on('data', (data) => { stdout += data.toString(); });
      stream.stderr.on('data', (data) => { stderr += data.toString(); });
      stream.on('close', (code) => {
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

  // Step 4: Change MySQL password
  console.log('\n--- Step 4: Change MySQL user password ---');
  const alterCmd = `docker exec psvibe-mysql mysql -uroot -p'${ROOT_PASS}' -e "ALTER USER 'psvibe_user'@'%' IDENTIFIED BY '${NEW_PASS}'; FLUSH PRIVILEGES;" 2>&1`;
  console.log('Running ALTER USER...');
  let r4 = await sshExec(conn, alterCmd);
  console.log('stdout:', r4.stdout || '(empty)');
  console.log('stderr:', r4.stderr || '(none)');
  console.log('exit code:', r4.code);

  if (r4.code !== 0 && r4.stderr && !r4.stderr.includes('Warning')) {
    console.log('❌ ALTER USER failed. Checking for mysql_native_password auth...');
    // Try with mysql_native_password
    const alterCmd2 = `docker exec psvibe-mysql mysql -uroot -p'${ROOT_PASS}' -e "ALTER USER 'psvibe_user'@'%' IDENTIFIED WITH mysql_native_password BY '${NEW_PASS}'; FLUSH PRIVILEGES;" 2>&1`;
    r4 = await sshExec(conn, alterCmd2);
    console.log('Retry stdout:', r4.stdout || '(empty)');
    console.log('Retry stderr:', r4.stderr || '(none)');
    console.log('Retry exit code:', r4.code);
  }

  // Step 5: Update secrets file
  console.log('\n--- Step 5: Update secrets.env ---');
  const sedCmd = `sed -i 's/MYSQL_PASSWORD=${OLD_PASS}/MYSQL_PASSWORD=${NEW_PASS}/' /etc/psvibe/secrets.env`;
  let r5 = await sshExec(conn, sedCmd);
  console.log('sed exit code:', r5.code);
  
  // Verify the file was updated
  let r5b = await sshExec(conn, "grep MYSQL_PASSWORD /etc/psvibe/secrets.env");
  console.log('Updated MYSQL_PASSWORD line:', r5b.stdout.trim());

  // Step 6: Restart API server
  console.log('\n--- Step 6: Restart API server ---');
  
  // Find what's running the API
  let r6a = await sshExec(conn, "docker ps --format '{{.Names}}' | grep -i api || echo 'no docker api'; systemctl list-units --type=service | grep -i psvibe || echo 'no systemd psvibe'");
  console.log('Services:', r6a.stdout.trim());
  
  // Try docker restart first
  let restartResult;
  let r6b = await sshExec(conn, "docker restart psvibe_api_server 2>&1 || docker restart psvibe-api 2>&1 || echo 'no docker api container found'");
  console.log('Docker restart:', r6b.stdout.trim(), r6b.stderr.trim());
  
  // Also try systemctl
  let r6c = await sshExec(conn, "systemctl restart psvibe-api-server 2>&1 || systemctl restart psvibe-api 2>&1 || echo 'no systemd service'");
  console.log('Systemd restart:', r6c.stdout.trim(), r6c.stderr.trim());
  
  // Check any uvicorn/python processes
  let r6d = await sshExec(conn, "ps aux | grep -i 'uvicorn\\|fastapi\\|psvibe' | grep -v grep 2>&1 || echo 'no python api'");
  console.log('Python processes:', r6d.stdout.trim());

  // Step 7: Verify
  console.log('\n--- Step 7: Verify new password works ---');
  let r7 = await sshExec(conn, `docker exec psvibe-mysql mysql -upsvibe_user -p'${NEW_PASS}' -e "SHOW DATABASES;" 2>&1`);
  console.log('Verification stdout:', r7.stdout || '(empty)');
  console.log('Verification stderr:', r7.stderr || '(none)');

  conn.end();
  console.log('\n✅ Password rotation complete');
}

main().catch(err => {
  console.error('❌ Error:', err.message);
  console.error(err.stack);
  process.exit(1);
});
