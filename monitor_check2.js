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
  // Find monitoring files/directories
  var commands = [
    'ls -la /root/coordination/ 2>&1 | head -40',
    'find /root -maxdepth 3 -name "check_alerts*" -o -name "health.log" -o -name "resources.log" -o -name "ratelimit.log" -o -name "uptime.log" -o -name "alert*" -type f 2>/dev/null | head -30',
    'find /root -maxdepth 2 -type d -name "monitoring" -o -name "monitor" -o -name "alerts" -o -name "findings" 2>/dev/null',
    'cat /root/coordination/check_alerts.py 2>&1 | head -50',
    'ls -la /root/coordination/findings/ 2>&1 | head -20'
  ];

  for (var i = 0; i < commands.length; i++) {
    console.log("\n===== CMD " + (i+1) + ": " + commands[i].substring(0,60) + "... =====");
    try {
      var r = await sshExec(commands[i]);
      console.log(r.stdout || '(empty)');
      if (r.stderr) console.log("STDERR: " + r.stderr);
    } catch(e) {
      console.log("ERROR: " + e.message);
    }
  }
}

main().catch(function(e) { console.error('FATAL: ' + e); });
