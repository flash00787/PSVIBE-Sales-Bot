#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const USERNAME = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const outputFile = '/home/node/.openclaw/workspace/temp/vps_api_fix.txt';
let fullLog = '';

function log(msg) {
  console.log(msg);
  fullLog += msg + '\n';
}

async function runCommand(conn, cmd, timeout = 15000) {
  return new Promise((resolve, reject) => {
    log(`\n--- CMD: ${cmd} ---`);
    let stdout = '', stderr = '';
    conn.exec(cmd, { timeout }, (err, stream) => {
      if (err) return reject(err);
      stream.on('data', (data) => { stdout += data.toString(); });
      stream.stderr.on('data', (data) => { stderr += data.toString(); });
      stream.on('close', (code) => {
        const out = (stdout + (stderr ? '\n[STDERR] ' + stderr : '')).trim();
        log(out);
        resolve({ code, stdout: stdout.trim(), stderr: stderr.trim(), output: out });
      });
    });
  });
}

async function main() {
  log('=== psvibe-api FIX SCRIPT ===');
  log(`Time: ${new Date().toISOString()}`);
  log(`Target: ${USERNAME}@${HOST}`);

  const conn = new Client();
  
  await new Promise((resolve, reject) => {
    conn.on('ready', () => {
      log('✅ SSH connected');
      resolve();
    });
    conn.on('error', (err) => {
      log(`❌ SSH error: ${err.message}`);
      reject(err);
    });
    conn.connect({
      host: HOST,
      username: USERNAME,
      privateKey: fs.readFileSync(KEY_PATH),
      readyTimeout: 10000,
      keepaliveInterval: 5000
    });
  });

  try {
    // 1. Check systemd status
    log('\n== STEP 1: Check service status ==');
    let systemdResult = await runCommand(conn, 'systemctl is-active psvibe-api 2>&1; systemctl status psvibe-api --no-pager -l 2>&1 | head -30');

    // 2. Check running processes
    log('\n== STEP 2: Check uvicorn processes ==');
    await runCommand(conn, 'ps aux | grep -i "[u]vicorn"');

    // 3. Check port 8000
    log('\n== STEP 3: Check port 8000 ==');
    await runCommand(conn, 'ss -tlnp | grep 8000 || netstat -tlnp 2>/dev/null | grep 8000');

    // 4. Check the API directory
    log('\n== STEP 4: Check API directory ==');
    await runCommand(conn, 'ls -la /root/psvibe_api_server/');

    // 5. Check run_sync.sh
    log('\n== STEP 5: Check run_sync.sh for start commands ==');
    await runCommand(conn, 'cat /root/psvibe_api_server/run_sync.sh');

    // 6. Try restarting
    log('\n== STEP 6: Restart service ==');
    if (systemdResult.stdout === 'active') {
      log('Service is active, attempting restart...');
    }
    let restartResult = await runCommand(conn, 'sudo systemctl restart psvibe-api 2>&1', 20000);

    // 7. If systemd restart didn't work well, try manual restart
    if (restartResult.code !== 0) {
      log('\n== STEP 6b: systemctl failed, trying manual restart ==');
      // Kill existing uvicorn
      await runCommand(conn, 'pkill -f "[u]vicorn" || true');
      await new Promise(r => setTimeout(r, 2000));
      // Check if it died
      await runCommand(conn, 'ps aux | grep -i "[u]vicorn" || echo "No uvicorn processes running"');
      // Start via systemd if available
      log('\n== STEP 6c: Try starting with systemctl ==');
      await runCommand(conn, 'sudo systemctl start psvibe-api 2>&1', 20000);
    }

    // 8. Wait and verify
    log('\n== STEP 7: Wait 5s and verify ==');
    await new Promise(r => setTimeout(r, 5000));
    await runCommand(conn, 'systemctl is-active psvibe-api 2>&1');
    await runCommand(conn, 'systemctl status psvibe-api --no-pager -l 2>&1 | head -20');
    await runCommand(conn, 'ss -tlnp | grep 8000 || echo "Port 8000 NOT listening"');

    // 9. Test the API
    log('\n== STEP 8: Test API endpoints ==');
    await runCommand(conn, 'curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>&1 || echo "health endpoint failed"');
    await runCommand(conn, 'curl -s --max-time 5 http://localhost:8000/health 2>&1 || echo "FAILED"');
    await runCommand(conn, 'curl -s --max-time 5 http://localhost:8000/ 2>&1 || echo "FAILED"');

    // Final check
    log('\n== FINAL STATUS ==');
    let finalActive = await runCommand(conn, 'systemctl is-active psvibe-api 2>&1');
    let finalListen = await runCommand(conn, 'ss -tlnp | grep ":8000"');

    const isActive = finalActive.stdout.includes('active');
    const isListening = finalListen.stdout.includes('8000');

    if (isActive && isListening) {
      log('\n=== RESULT: OK ===');
      log('psvibe-api is ACTIVE and LISTENING on port 8000');
    } else {
      log(`\n=== RESULT: WARN ===`);
      log(`Active: ${finalActive.stdout}, Listening: ${isListening ? 'YES' : 'NO'}`);
      // Try one more thing - start manually if systemd is being difficult
      if (!isListening) {
        log('\n== Attempting manual start via uvicorn... ==');
        // Check if there's a venv and start manually
        await runCommand(conn, 'cd /root/psvibe_api_server && ls -la venv/bin/python3 2>/dev/null && nohup venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /var/log/psvibe-api-manual.log 2>&1 & echo "PID=$!"');
        await new Promise(r => setTimeout(r, 5000));
        await runCommand(conn, 'ss -tlnp | grep ":8000" || echo "Still not listening"');
        let finalTest = await runCommand(conn, 'curl -s --max-time 5 http://localhost:8000/health 2>&1');
        if (finalTest.stdout && !finalTest.stdout.includes('FAIL')) {
          log('\n=== RESULT: OK (manual start) ===');
        } else {
          log('\n=== RESULT: ERROR - API still not responding even after manual start ===');
        }
      }
    }

  } catch (e) {
    log(`\n❌ CRITICAL ERROR: ${e.message}`);
    log('\n=== RESULT: ERROR - Script execution failed ===');
  } finally {
    conn.end();
    fs.writeFileSync(outputFile, fullLog);
    log(`\nFull log written to ${outputFile}`);
  }
}

main().catch(e => {
  console.error('Fatal:', e);
  process.exit(1);
});
