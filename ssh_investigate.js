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
      label: 'MySQL status',
      cmd: 'systemctl status mysql --no-pager 2>&1; systemctl status mariadb --no-pager 2>&1; ps aux | grep -i mysql 2>&1',
    },
    {
      label: 'MySQL socket',
      cmd: 'ls -la /run/mysqld/ 2>&1; ls -la /var/run/mysqld/ 2>&1; find / -name "mysqld.sock" 2>/dev/null; find / -name "*.sock" -path "*mysql*" 2>/dev/null',
    },
    {
      label: 'MySQL via TCP',
      cmd: 'mysql -u root -h 127.0.0.1 -e "SHOW DATABASES;" 2>&1',
    },
    {
      label: 'SHOW TABLES psvibe',
      cmd: 'mysql -u root -h 127.0.0.1 --database=psvibe -e "SHOW TABLES;" 2>&1',
    },
    {
      label: 'DESCRIBE sales_daily',
      cmd: 'mysql -u root -h 127.0.0.1 --database=psvibe -e "DESCRIBE sales_daily;" 2>&1',
    },
    {
      label: 'SELECT sales_daily LIMIT 3',
      cmd: 'mysql -u root -h 127.0.0.1 --database=psvibe -e "SELECT * FROM sales_daily LIMIT 3;" 2>&1',
    },
    {
      label: 'SHOW TABLES psvibe_dashboard',
      cmd: 'mysql -u root -h 127.0.0.1 --database=psvibe_dashboard -e "SHOW TABLES;" 2>&1',
    },
    {
      label: 'DESCRIBE opex',
      cmd: 'mysql -u root -h 127.0.0.1 --database=psvibe_dashboard -e "DESCRIBE opex;" 2>&1',
    },
    {
      label: 'SELECT opex LIMIT 5',
      cmd: 'mysql -u root -h 127.0.0.1 --database=psvibe_dashboard -e "SELECT * FROM opex LIMIT 5;" 2>&1',
    },
    {
      label: 'DESCRIBE cash_movements',
      cmd: 'mysql -u root -h 127.0.0.1 --database=psvibe_dashboard -e "DESCRIBE cash_movements;" 2>&1',
    },
    {
      label: 'SELECT cash_movements',
      cmd: 'mysql -u root -h 127.0.0.1 --database=psvibe_dashboard -e "SELECT * FROM cash_movements;" 2>&1',
    },
    {
      label: 'DESCRIBE income_by_acct',
      cmd: 'mysql -u root -h 127.0.0.1 --database=psvibe_dashboard -e "DESCRIBE income_by_acct;" 2>&1',
    },
    {
      label: 'SELECT income_by_acct',
      cmd: 'mysql -u root -h 127.0.0.1 --database=psvibe_dashboard -e "SELECT * FROM income_by_acct;" 2>&1',
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
