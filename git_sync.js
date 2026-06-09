const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const privateKey = fs.readFileSync(KEY_PATH, 'utf8');

function runCmd(client, cmd) {
  return new Promise((resolve, reject) => {
    client.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '';
      let stderr = '';
      stream.on('data', (d) => { stdout += d.toString(); });
      stream.stderr.on('data', (d) => { stderr += d.toString(); });
      stream.on('close', (code) => {
        resolve({ stdout, stderr, code });
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
      username: USER,
      privateKey: privateKey,
      readyTimeout: 10000,
    });
  });

  const outputLines = [];
  outputLines.push('=== GIT SYNC RESULT ===');
  outputLines.push(`Date: ${new Date().toISOString()}`);
  outputLines.push('');

  try {
    // Step 1: Git Status
    outputLines.push('--- Step 1: Git Status ---');
    
    let r = await runCmd(conn, 'cd /root/psvibe-sales-bot && git status --short');
    outputLines.push(`[psvibe-sales-bot] status:\n${r.stdout || '(clean)'}`);
    if (r.stderr) outputLines.push(`[psvibe-sales-bot] stderr:\n${r.stderr}`);
    outputLines.push(`exit code: ${r.code}`);
    outputLines.push('');

    r = await runCmd(conn, 'cd /root/psvibe_api_server && git status --short');
    outputLines.push(`[psvibe_api_server] status:\n${r.stdout || '(clean)'}`);
    if (r.stderr) outputLines.push(`[psvibe_api_server] stderr:\n${r.stderr}`);
    outputLines.push(`exit code: ${r.code}`);
    outputLines.push('');

    // Step 2: Git config + commit + push for psvibe-sales-bot
    outputLines.push('--- Step 2: psvibe-sales-bot commit + push ---');
    
    // Ensure git config
    await runCmd(conn, 'cd /root/psvibe-sales-bot && git config user.name "Kora" && git config user.email "chanmyint123456789@gmail.com"');
    outputLines.push('Git config set for psvibe-sales-bot');

    r = await runCmd(conn, 'cd /root/psvibe-sales-bot && git add -A && git diff --cached --quiet || echo "HAS_CHANGES"');
    if (r.stdout.includes('HAS_CHANGES')) {
      r = await runCmd(conn, 'cd /root/psvibe-sales-bot && git commit -m "fix: add missing _replit_patch and _replit_put helpers"');
      outputLines.push(`Commit output:\n${r.stdout}`);
      if (r.stderr) outputLines.push(`stderr:\n${r.stderr}`);
      outputLines.push(`exit code: ${r.code}`);

      r = await runCmd(conn, 'cd /root/psvibe-sales-bot && git push');
      outputLines.push(`Push output:\n${r.stdout}`);
      if (r.stderr) outputLines.push(`stderr:\n${r.stderr}`);
      outputLines.push(`exit code: ${r.code}`);
    } else {
      outputLines.push('Nothing to commit (no changes detected for psvibe-sales-bot)');
    }
    outputLines.push('');

    // Step 3: Git config + commit + push for psvibe_api_server
    outputLines.push('--- Step 3: psvibe_api_server commit + push ---');

    await runCmd(conn, 'cd /root/psvibe_api_server && git config user.name "Kora" && git config user.email "chanmyint123456789@gmail.com"');
    outputLines.push('Git config set for psvibe_api_server');

    r = await runCmd(conn, 'cd /root/psvibe_api_server && git add -A && git diff --cached --quiet || echo "HAS_CHANGES"');
    if (r.stdout.includes('HAS_CHANGES')) {
      r = await runCmd(conn, 'cd /root/psvibe_api_server && git commit -m "fix: remove duplicate /api/bookings/search endpoint"');
      outputLines.push(`Commit output:\n${r.stdout}`);
      if (r.stderr) outputLines.push(`stderr:\n${r.stderr}`);
      outputLines.push(`exit code: ${r.code}`);

      r = await runCmd(conn, 'cd /root/psvibe_api_server && git push');
      outputLines.push(`Push output:\n${r.stdout}`);
      if (r.stderr) outputLines.push(`stderr:\n${r.stderr}`);
      outputLines.push(`exit code: ${r.code}`);
    } else {
      outputLines.push('Nothing to commit (no changes detected for psvibe_api_server)');
    }
    outputLines.push('');

    // Step 4: Verify
    outputLines.push('--- Step 4: Verify recent commits ---');

    r = await runCmd(conn, 'cd /root/psvibe-sales-bot && git log --oneline -3');
    outputLines.push(`[psvibe-sales-bot] recent commits:\n${r.stdout}`);
    outputLines.push('');

    r = await runCmd(conn, 'cd /root/psvibe_api_server && git log --oneline -3');
    outputLines.push(`[psvibe_api_server] recent commits:\n${r.stdout}`);
    outputLines.push('');

  } catch (err) {
    outputLines.push(`ERROR: ${err.message}`);
    outputLines.push(err.stack || '');
  } finally {
    conn.end();
  }

  const result = outputLines.join('\n');
  console.log(result);

  // Write result to file on remote
  const conn2 = new Client();
  await new Promise((resolve, reject) => {
    conn2.on('ready', resolve);
    conn2.on('error', reject);
    conn2.connect({
      host: HOST,
      username: USER,
      privateKey: privateKey,
      readyTimeout: 10000,
    });
  });

  // Escape for shell
  const escaped = result.replace(/'/g, "'\\''");
  await runCmd(conn2, `cat > /root/git_sync_result.md << 'EOF'\n${result}\nEOF`);
  conn2.end();
  console.log('Result written to /root/git_sync_result.md');
}

main().catch(err => {
  console.error('FATAL:', err);
  process.exit(1);
});
