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
      label: 'Docker MySQL env',
      cmd: 'grep -r "MYSQL_ROOT_PASSWORD\|mysql.*password\|DB_PASS\|MYSQL_PASSWORD" /root/psvibe_api_server/ --include="*.py" --include="*.env" --include="*.json" --include="*.yml" --include="*.yaml" -l 2>/dev/null; echo "---"; cat /root/psvibe_api_server/.env 2>/dev/null; echo "---"; grep -r "mysql\|MYSQL" /root/docker-compose*.yml /root/*/docker-compose*.yml 2>/dev/null | head -30',
    },
    {
      label: 'API server config',
      cmd: 'grep -n "mysql\|MYSQL\|password\|DB_\|_mysql" /root/psvibe_api_server/config.py 2>/dev/null | head -30; echo "==="; grep -n "_mysql_query\|mysql" /root/psvibe_api_server/dashboard_routes.py | head -20',
    },
    {
      label: 'Docker ps + compose',
      cmd: 'docker ps 2>&1; echo "==="; docker ps --format "{{.Names}}" 2>&1; echo "==="; ls /root/docker-compose*.yml /root/*/docker-compose*.yml /opt/*/docker-compose*.yml 2>/dev/null',
    },
    {
      label: 'Find mysql in docker',
      cmd: 'docker ps --format "{{.Names}} {{.Image}}" 2>&1 | grep -i mysql; echo "==="; docker inspect $(docker ps -q --filter "ancestor=mysql" 2>/dev/null) 2>/dev/null | grep -A5 "MYSQL_ROOT_PASSWORD" | head -20',
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
