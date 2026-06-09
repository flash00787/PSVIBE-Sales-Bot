const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '167.71.196.120';
const PORT = 22;
const USERNAME = 'root';
const PRIVATE_KEY_PATH = path.join(__dirname, '.ssh', 'id_rsa');
const SRC = '/root/staging/bot_src/bot/handlers';
const DST = '/root/Sales-Tele-Bot_refactored/bot/handlers';
const FILES = ['sales.py', 'members.py', 'referral.py', 'discount.py'];

function sshExec(conn, cmd, timeout = 30000) {
  return new Promise((resolve, reject) => {
    let stdout = '', stderr = '';
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      stream.on('data', (data) => { stdout += data.toString(); });
      stream.stderr.on('data', (data) => { stderr += data.toString(); });
      stream.on('close', (code) => {
        resolve({ code, stdout, stderr });
      });
    });
  });
}

function connect() {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => resolve(conn));
    conn.on('error', reject);
    conn.connect({
      host: HOST,
      port: PORT,
      username: USERNAME,
      privateKey: fs.readFileSync(PRIVATE_KEY_PATH),
    });
  });
}

async function main() {
  const conn = await connect();
  console.log('=== Connected to VPS ===\n');

  // Step 5: Deploy via rsync (equivalent using cp for safety)
  console.log('--- STEP 5: Deploy ---');
  for (const f of FILES) {
    // Backup existing
    await sshExec(conn, `cp ${DST}/${f} ${DST}/${f}.bak 2>/dev/null; echo "backed up"`);
    // Copy (simulate rsync with cp)
    let r = await sshExec(conn, `cp ${SRC}/${f} ${DST}/${f} && echo "DEPLOYED: ${f}" || echo "FAILED: ${f}"`);
    console.log(r.stdout.trim());
    // Verify file was copied
    r = await sshExec(conn, `wc -l ${DST}/${f}`);
    console.log(`  Lines: ${r.stdout.trim()}`);
  }

  // Step 6: Restart the service
  console.log('\n--- STEP 6: Restart service ---');
  let r = await sshExec(conn, `systemctl restart psvibe-bot-refactored.service && echo "RESTART OK" || echo "RESTART FAILED"`, 15000);
  console.log(r.stdout.trim());
  if (r.stderr) console.log('stderr:', r.stderr.trim());

  // Wait a moment for the bot to start
  await new Promise(r => setTimeout(r, 3000));

  // Check service status
  r = await sshExec(conn, `systemctl is-active psvibe-bot-refactored.service`);
  console.log(`Service status: ${r.stdout.trim()}`);

  // Step 7: Check logs
  console.log('\n--- STEP 7: Logs (last 25 lines) ---');
  r = await sshExec(conn, `tail -25 /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null || echo "LOG NOT FOUND"`);
  console.log(r.stdout);

  conn.end();
  console.log('\n=== DONE ===');
}

main().catch(err => {
  console.error('FATAL:', err);
  process.exit(1);
});
