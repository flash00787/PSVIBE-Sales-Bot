const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const conn = new Client();

conn.on('ready', () => {
  const results = {};

  // Step 1: Run check_alerts.sh
  conn.exec('/root/monitoring/check_alerts.sh', (err, stream) => {
    if (err) {
      results.alertOutput = `ERROR: ${err.message}`;
      afterStep1();
      return;
    }
    let output = '';
    stream.on('data', (data) => { output += data.toString(); });
    stream.stderr.on('data', (data) => { output += data.toString(); });
    stream.on('close', (code) => {
      results.alertOutput = output.trim();
      results.alertExitCode = code;
      afterStep1();
    });
  });

  function afterStep1() {
    // Step 2: Check last 3 lines of health.log, resources.log, ratelimit.log, uptime.log
    const logFiles = [
      '/root/monitoring/health.log',
      '/root/monitoring/resources.log',
      '/root/monitoring/ratelimit.log',
      '/root/monitoring/uptime.log'
    ];

    let pending = logFiles.length;
    const logResults = {};

    logFiles.forEach((file) => {
      conn.exec(`tail -3 ${file} 2>&1`, (err, stream) => {
        if (err) {
          logResults[file] = `ERROR: ${err.message}`;
          pending--;
          if (pending === 0) afterAll();
          return;
        }
        let output = '';
        stream.on('data', (data) => { output += data.toString(); });
        stream.stderr.on('data', (data) => { output += data.toString(); });
        stream.on('close', () => {
          logResults[file] = output.trim();
          pending--;
          if (pending === 0) afterAll();
        });
      });
    });

    function afterAll() {
      // Output combined result as JSON
      const combined = { alerts: results, logs: logResults };
      console.log(JSON.stringify(combined, null, 2));
      conn.end();
    }
  }
}).connect({
  host: HOST,
  port: 22,
  username: USER,
  privateKey: KEY,
  readyTimeout: 15000
});
