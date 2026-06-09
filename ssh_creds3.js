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

async function runAll() {
  const commands = [
    {
      label: 'docker inspect mysql env',
      cmd: 'docker inspect psvibe-mysql 2>&1 | python3 -c "\nimport sys, json\ndata = json.load(sys.stdin)[0]\nenv = data.get(\"Config\", {}).get(\"Env\", [])\nfor e in env:\n    print(e)\n" 2>&1',
    },
    {
      label: 'API server db module find',
      cmd: 'ls /root/psvibe_api_server/*.py 2>/dev/null; echo "==="; grep -rn "mysql\|MYSQL\|pymysql\|connect" /root/psvibe_api_server/*.py 2>/dev/null | grep -v "^Binary" | head -40',
    },
    {
      label: 'openclaw compose for mysql',
      cmd: 'cat /root/openclaw/docker-compose.yml 2>/dev/null | head -80',
    },
  ];

  for (const { label, cmd } of commands) {
    console.log(`\n=== ${label} ===`);
    try {
      const r = await sshExec(cmd, 30000);
      console.log(`Exit: ${r.code}`);
      console.log(r.stdout);
      if (r.stderr) console.log('STDERR:', r.stderr);
    } catch (e) {
      console.log(`ERROR: ${e.message}`);
    }
  }
}

runAll().catch(e => console.error('FATAL:', e));
