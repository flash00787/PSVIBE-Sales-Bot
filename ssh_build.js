const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = path.join(__dirname, '.ssh', 'id_rsa');

async function sshExec(command, timeout = 120000) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let output = '';
    let errOutput = '';
    let timer = setTimeout(() => {
      conn.end();
      reject(new Error(`Timeout after ${timeout}ms: ${command.substring(0,100)}`));
    }, timeout);

    conn.on('ready', () => {
      conn.exec(command, (err, stream) => {
        if (err) {
          clearTimeout(timer);
          conn.end();
          return reject(err);
        }
        stream.on('close', (code, signal) => {
          clearTimeout(timer);
          conn.end();
          resolve({ code, stdout: output, stderr: errOutput });
        }).on('data', (data) => { output += data.toString(); })
          .stderr.on('data', (data) => { errOutput += data.toString(); });
      });
    });

    conn.on('error', (err) => {
      clearTimeout(timer);
      reject(err);
    });

    conn.connect({
      host: HOST,
      port: 22,
      username: USER,
      privateKey: fs.readFileSync(KEY_PATH),
      readyTimeout: 15000,
    });
  });
}

async function runDeploy() {
  const cmds = [
    {
      label: 'npm build',
      cmd: 'cd /root/psvibe-dashboard && npm run build 2>&1',
      timeout: 180000,
    },
  ];

  for (const { label, cmd, timeout } of cmds) {
    console.log(`\n=== ${label} ===`);
    try {
      const r = await sshExec(cmd, timeout || 120000);
      console.log(`Exit: ${r.code}`);
      // Show last 50 lines of output
      const lines = r.stdout.split('\n');
      console.log(lines.slice(-50).join('\n'));
      if (r.stderr && r.code !== 0) console.log('STDERR:', r.stderr.slice(-500));
    } catch (e) {
      console.log(`ERROR: ${e.message}`);
    }
  }
}

runDeploy().catch(e => console.error('FATAL:', e));
