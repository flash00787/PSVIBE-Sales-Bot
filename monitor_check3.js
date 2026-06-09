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
  // Use single-quoted path with escaped inner single quotes
  var MON = "'/root/Aung Chan Myint/monitoring'";

  // 1. Run check_alerts.sh
  console.log("===== 1. check_alerts.sh =====");
  try {
    var r = await sshExec('bash ' + MON + '/check_alerts.sh 2>&1');
    console.log("STDOUT: " + r.stdout);
    if (r.stderr) console.log("STDERR: " + r.stderr);
    console.log("EXIT CODE: " + r.code);
  } catch(e) {
    console.log("ERROR: " + e.message);
  }

  // 2. Content of check_alerts.sh
  console.log("\n===== 2. check_alerts.sh CONTENT =====");
  try {
    r = await sshExec('cat ' + MON + '/check_alerts.sh 2>&1');
    console.log(r.stdout);
  } catch(e) {
    console.log("ERROR: " + e.message);
  }

  // 3. Log files
  var logs = ['health.log', 'resources.log', 'ratelimit.log', 'uptime.log'];
  for (var i = 0; i < logs.length; i++) {
    console.log("\n===== 3." + (i+1) + " " + logs[i] + " (last 3 lines) =====");
    try {
      r = await sshExec('tail -n 3 ' + MON + '/' + logs[i] + ' 2>&1');
      console.log(r.stdout || '(empty)');
      if (r.stderr) console.log("STDERR: " + r.stderr);
    } catch(e) {
      console.log("ERROR: " + e.message);
    }
  }

  // 4. Full log sizes and dates
  console.log("\n===== 4. Log file sizes & dates =====");
  try {
    r = await sshExec('ls -la ' + MON + '/ 2>&1');
    console.log(r.stdout);
  } catch(e) {
    console.log("ERROR: " + e.message);
  }

  // 5. Any alert files in the monitoring dir
  console.log("\n===== 5. Alert-related files =====");
  try {
    r = await sshExec('ls -la ' + MON + '/alert* ' + MON + '/*alert* 2>&1');
    console.log(r.stdout);
  } catch(e) {
    console.log("(none or error)");
  }
}

main().catch(function(e) { console.error('FATAL: ' + e); });
