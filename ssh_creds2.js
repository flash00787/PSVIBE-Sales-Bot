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
      label: 'Find compose with mysql',
      cmd: 'grep -rl "psvibe.*mysql\|mysql.*psvibe\|psvibe-mysql" /root/ /opt/ 2>/dev/null; echo "==="; find /root -name "docker-compose*.yml" -exec grep -l "mysql\|MYSQL" {} \\; 2>/dev/null',
    },
    {
      label: 'psvibe docker compose',
      cmd: 'cat /root/psvibe-docker-compose.yml 2>/dev/null; echo "==="; cat /root/docker-compose.yml 2>/dev/null; echo "==="; cat /root/psvibe/docker-compose.yml 2>/dev/null; echo "==="; cat /root/psvibe_api_server/docker-compose.yml 2>/dev/null',
    },
    {
      label: 'find compose files everywhere',
      cmd: 'find / -maxdepth 4 -name "docker-compose*.yml" -o -name "docker-compose*.yaml" 2>/dev/null | grep -v overlayfs | grep -v "\.Trash" | head -20',
    },
    {
      label: 'inspect mysql container env',
      cmd: 'docker inspect psvibe-mysql 2>&1 | python3 -c "import sys,json; c=json.load(sys.stdin)[0]; [print(k,v) for k,v in c[\"Config\"][\"Env\"] if \"PASSWORD\" in k.upper() or \"MYSQL\" in k.upper() or \"ROOT\" in k.upper()]" 2>&1',
    },
    {
      label: 'API DB config',
      cmd: 'find /root/psvibe_api_server -name "*.py" -exec grep -l "mysql\|MySQL\|_mysql_query\|pymysql\|mysql\.connector" {} \\; 2>/dev/null; echo "==="; grep -rn "host.*=.*\|password.*=.*\|user.*=.*\|database.*=.*" /root/psvibe_api_server/db.py 2>/dev/null; echo "==="; cat /root/psvibe_api_server/db.py 2>/dev/null | head -60',
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
