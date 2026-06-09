const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const host = '5.223.81.16';
const username = 'root';
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

function execCommand(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', (data) => { stdout += data.toString(); });
      stream.stderr.on('data', (data) => { stderr += data.toString(); });
      stream.on('close', (code) => {
        resolve({ code, stdout, stderr });
      });
    });
  });
}

async function runAll() {
  const results = {};
  const outDir = '/home/node/.openclaw/workspace/temp';

  return new Promise((resolve, reject) => {
    const conn = new Client();
    let connected = false;
    const timeout = setTimeout(() => {
      if (!connected) {
        conn.end();
        reject(new Error('Connection timeout'));
      }
    }, 15000);

    conn.on('ready', async () => {
      connected = true;
      clearTimeout(timeout);
      console.log('=== CONNECTED ===');

      try {
        // 1. journalctl
        console.log('\n--- STEP 1: journalctl ---');
        const r1 = await execCommand(conn, 'journalctl -u psvibe-sale-bot.service --no-pager -n 100 2>&1');
        results.journalctl = r1.stdout + (r1.stderr ? '\nSTDERR:\n' + r1.stderr : '');
        fs.writeFileSync(path.join(outDir, 'tu_journalctl.txt'), results.journalctl);
        console.log('journalctl done, length:', results.journalctl.length);

        // 2. Read members.py
        console.log('\n--- STEP 2: Read members.py ---');
        const r2 = await execCommand(conn, 'cat /root/psvibe-sales-bot/bot/handlers/members.py 2>&1');
        results.members_py = r2.stdout;
        fs.writeFileSync(path.join(outDir, 'tu_members_py.txt'), results.members_py);
        console.log('members.py done, length:', results.members_py.length);

        // 3. Read app.py (lines around 150-180)
        console.log('\n--- STEP 3: Read app.py ---');
        const r3 = await execCommand(conn, 'cat /root/psvibe-sales-bot/bot/app.py 2>&1');
        results.app_py = r3.stdout;
        fs.writeFileSync(path.join(outDir, 'tu_app_py.txt'), results.app_py);
        console.log('app.py done, length:', results.app_py.length);

        // 4. Read __init__.py (around line 1100)
        console.log('\n--- STEP 4: Read __init__.py ---');
        const r4 = await execCommand(conn, 'cat /root/psvibe-sales-bot/bot/__init__.py 2>&1');
        results.init_py = r4.stdout;
        fs.writeFileSync(path.join(outDir, 'tu_init_py.txt'), results.init_py);
        console.log('__init__.py done, length:', results.init_py.length);

        // 5. systemctl status
        console.log('\n--- STEP 5: systemctl status ---');
        const r5 = await execCommand(conn, 'systemctl status psvibe-sale-bot.service 2>&1');
        results.service_status = r5.stdout + (r5.stderr ? '\nSTDERR:\n' + r5.stderr : '');
        fs.writeFileSync(path.join(outDir, 'tu_service_status.txt'), results.service_status);
        console.log('service status done');

        // 6. Syntax check
        console.log('\n--- STEP 6: Syntax check ---');
        const r6 = await execCommand(conn, 'cd /root/psvibe-sales-bot && python3 -c "import ast; ast.parse(open(\'bot/handlers/members.py\').read()); print(\'SYNTAX OK\')" 2>&1');
        results.syntax_check = r6.stdout + (r6.stderr ? '\nSTDERR:\n' + r6.stderr : '');
        fs.writeFileSync(path.join(outDir, 'tu_syntax_check.txt'), results.syntax_check);
        console.log('syntax check done');

        // Save all results metadata
        fs.writeFileSync(path.join(outDir, 'tu_all_results.json'), JSON.stringify({
          steps_completed: Object.keys(results),
          timestamp: new Date().toISOString()
        }, null, 2));
        console.log('\n=== ALL DONE ===');

      } catch (e) {
        console.error('Error during execution:', e.message);
        results.error = e.message;
      }

      conn.end();
      resolve(results);
    });

    conn.on('error', (err) => {
      clearTimeout(timeout);
      connected = true;
      console.error('Connection error:', err.message);
      reject(err);
    });

    conn.connect({ host, username, privateKey });
  });
}

runAll()
  .then(() => { console.log('\nSUCCESS'); process.exit(0); })
  .catch((e) => { console.error('\nFAILED:', e.message); process.exit(1); });
