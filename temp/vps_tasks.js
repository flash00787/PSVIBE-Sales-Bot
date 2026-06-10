const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const RESULTS_FILE = '/home/node/.openclaw/workspace/temp/vps_results.json';

const results = {
  quality_gate: { status: 'PENDING', output: '', error: '' },
  coordination_audit: { status: 'PENDING', files: [], missing: [], output: '' },
  git_sales_bot: { status: 'PENDING', output: '', error: '' },
  git_api_server: { status: 'PENDING', output: '', error: '' }
};

function execCommand(conn, cmd, timeout = 60000) {
  return new Promise((resolve, reject) => {
    let output = '';
    let errOutput = '';
    const timer = setTimeout(() => {
      reject(new Error(`Command timed out after ${timeout}ms: ${cmd}`));
    }, timeout);

    conn.exec(cmd, (err, stream) => {
      if (err) { clearTimeout(timer); reject(err); return; }
      stream.on('data', (data) => { output += data.toString(); });
      stream.stderr.on('data', (data) => { errOutput += data.toString(); });
      stream.on('close', (code) => {
        clearTimeout(timer);
        resolve({ code, stdout: output, stderr: errOutput });
      });
    });
  });
}

async function runAllTasks() {
  const conn = new Client();
  
  return new Promise((resolve, reject) => {
    conn.on('ready', async () => {
      console.log('SSH Connected');
      
      try {
        // === TASK 1: Quality Gate ===
        console.log('\n=== TASK 1: Quality Gate ===');
        try {
          const qg = await execCommand(conn, 'python3 /root/coordination/quality_gate.py --quick 2>&1');
          results.quality_gate.output = (qg.stdout + qg.stderr).trim();
          results.quality_gate.exitCode = qg.code;
          results.quality_gate.status = qg.code === 0 ? 'OK' : 'FAIL';
          console.log('Quality gate exit code:', qg.code);
          console.log(results.quality_gate.output.slice(-500));
        } catch(e) {
          results.quality_gate.status = 'ERROR';
          results.quality_gate.error = e.message;
          console.error('Quality gate error:', e.message);
        }

        // === TASK 2: Coordination Tools Audit ===
        console.log('\n=== TASK 2: Coordination Tools Audit ===');
        try {
          const ls = await execCommand(conn, 'ls -la /root/coordination/ 2>&1');
          results.coordination_audit.output = (ls.stdout + ls.stderr).trim();
          
          const expected = [
            'quality_gate.py', 'fix_protocol.py', 'auto_doc_updater.py',
            'tool_orchestrator.py', 'workflow_engine.py', 'notifier.py',
            'queue_manager.py', 'check_alerts.py', 'task_bridge.py',
            'auto_bug_fixer.py', 'auto_healer.py'
          ];
          
          const existing = results.coordination_audit.output;
          results.coordination_audit.files = expected.filter(f => existing.includes(f));
          results.coordination_audit.missing = expected.filter(f => !existing.includes(f));
          results.coordination_audit.status = results.coordination_audit.missing.length === 0 ? 'OK' : 'PARTIAL';
          console.log('Existing:', results.coordination_audit.files);
          console.log('Missing:', results.coordination_audit.missing);
        } catch(e) {
          results.coordination_audit.status = 'ERROR';
          results.coordination_audit.error = e.message;
        }

        // === TASK 3: Git Auto-Sync Sales Bot ===
        console.log('\n=== TASK 3: Git Auto-Sync Sales Bot ===');
        try {
          const git1 = await execCommand(conn, 
            'cd /root/psvibe-sales-bot && git add -A && git commit -m "auto-sync: phase2 upgrades $(date +%Y-%m-%d)" && git push 2>&1', 
            120000);
          results.git_sales_bot.output = (git1.stdout + git1.stderr).trim();
          results.git_sales_bot.exitCode = git1.code;
          results.git_sales_bot.status = git1.code === 0 ? 'OK' : 'FAIL';
          console.log(results.git_sales_bot.output.slice(-500));
        } catch(e) {
          results.git_sales_bot.status = 'ERROR';
          results.git_sales_bot.error = e.message;
        }

        // === TASK 4: Git Auto-Sync API Server ===
        console.log('\n=== TASK 4: Git Auto-Sync API Server ===');
        try {
          const git2 = await execCommand(conn, 
            'cd /root/psvibe_api_server && git add -A && git commit -m "auto-sync: phase2 upgrades $(date +%Y-%m-%d)" && git push 2>&1', 
            120000);
          results.git_api_server.output = (git2.stdout + git2.stderr).trim();
          results.git_api_server.exitCode = git2.code;
          results.git_api_server.status = git2.code === 0 ? 'OK' : 'FAIL';
          console.log(results.git_api_server.output.slice(-500));
        } catch(e) {
          results.git_api_server.status = 'ERROR';
          results.git_api_server.error = e.message;
        }

      } catch(e) {
        console.error('Task error:', e);
      }
      
      conn.end();
      fs.writeFileSync(RESULTS_FILE, JSON.stringify(results, null, 2));
      resolve(results);
    });

    conn.on('error', (err) => {
      results.quality_gate.status = 'CONNECTION_ERROR';
      results.quality_gate.error = err.message;
      fs.writeFileSync(RESULTS_FILE, JSON.stringify(results, null, 2));
      reject(err);
    });

    conn.connect({
      host: HOST,
      port: 22,
      username: 'root',
      privateKey: fs.readFileSync(KEY_PATH),
      readyTimeout: 15000
    });
  });
}

runAllTasks()
  .then(r => { console.log('\n=== ALL DONE ==='); console.log(JSON.stringify(r, null, 2)); })
  .catch(e => { console.error('\n=== FATAL ===', e.message); });
