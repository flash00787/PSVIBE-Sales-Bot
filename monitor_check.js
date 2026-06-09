const { Client } = require('ssh2');
const fs = require('fs');
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const HOST = '5.223.81.16';

function sshExec(command, timeout) {
  timeout = timeout || 30000;
  return new Promise(function(resolve, reject) {
    var conn = new Client();
    var stdout = '';
    var stderr = '';
    var timer = setTimeout(function() { conn.end(); reject(new Error('Timeout')); }, timeout);
    conn.on('ready', function() {
      conn.exec(command, function(e, stream) {
        if (e) { clearTimeout(timer); conn.end(); return reject(e); }
        stream.on('data', function(d) { stdout += d.toString(); });
        stream.stderr.on('data', function(d) { stderr += d.toString(); });
        stream.on('close', function(code) {
          clearTimeout(timer);
          conn.end();
          resolve({ stdout: stdout, stderr: stderr, code: code });
        });
      });
    });
    conn.on('error', function(e) { clearTimeout(timer); reject(e); });
    conn.connect({ host: HOST, port: 22, username: 'root', privateKey: fs.readFileSync(KEY_PATH), readyTimeout: 15000 });
  });
}

async function main() {
  // 1. Run check_alerts.sh
  console.log("===== CHECK ALERTS =====");
  try {
    var r = await sshExec('bash /root/monitoring/check_alerts.sh 2>&1');
    console.log("STDOUT: " + r.stdout);
    console.log("STDERR: " + r.stderr);
    console.log("EXIT: " + r.code);
  } catch(e) {
    console.log("ERROR: " + e.message);
  }

  // 2. Check log files
  var logs = ['health.log', 'resources.log', 'ratelimit.log', 'uptime.log'];
  for (var i = 0; i < logs.length; i++) {
    var logFile = '/root/monitoring/' + logs[i];
    console.log("\n===== " + logFile + " (last 3 lines) =====");
    try {
      r = await sshExec('tail -3 ' + logFile + ' 2>&1');
      console.log(r.stdout || '(empty)');
      if (r.stderr) console.log("STDERR: " + r.stderr);
    } catch(e) {
      console.log("ERROR: " + e.message);
    }
  }

  // 3. Directory listing
  console.log("\n===== /root/monitoring/ directory =====");
  try {
    r = await sshExec('ls -la /root/monitoring/ 2>&1');
    console.log(r.stdout);
  } catch(e) {
    console.log("ERROR: " + e.message);
  }
}

main().catch(function(e) { console.error('FATAL: ' + e); });
