const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = path.join(__dirname, '.ssh', 'id_rsa');

async function sshExec(command, timeout = 60000) {
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
      label: 'Login and get token',
      cmd: `TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','NO_TOKEN'))" 2>&1) && echo "TOKEN=$TOKEN" && curl -s http://localhost:8000/api/dashboard/finance/balances -H "Authorization: Bearer $TOKEN" 2>&1 | python3 -m json.tool 2>&1`,
      timeout: 15000,
    },
  ];

  for (const { label, cmd, timeout } of cmds) {
    console.log(`\n=== ${label} ===`);
    try {
      const r = await sshExec(cmd, timeout || 60000);
      console.log(`Exit: ${r.code}`);
      console.log(r.stdout);
      if (r.stderr) console.log('STDERR:', r.stderr);
    } catch (e) {
      console.log(`ERROR: ${e.message}`);
    }
  }
}

runDeploy().catch(e => console.error('FATAL:', e));
