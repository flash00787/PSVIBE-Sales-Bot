const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // MySQL via TCP
  'mysql -uroot -h 127.0.0.1 psvibe_api -e "SHOW COLUMNS FROM console_booking" 2>&1',
  // Check MySQL password config
  'grep -i mysql /etc/psvibe/secrets.env 2>/dev/null',
  // Check if MySQL is running
  'systemctl status mysql 2>&1 | head -5 || systemctl status mariadb 2>&1 | head -5',
  // Check what the API uses for MySQL connection  
  'grep -n "mysql_connect\|MySQLdb\|pymysql\|mysql\.connector" /root/psvibe_api_server/app.py | head -5',
];

let results = {};
let cmdIdx = 0;

conn.on('ready', () => runNext());
function runNext() {
  if (cmdIdx >= commands.length) { conn.end(); console.log(JSON.stringify(results, null, 2)); return; }
  const cmd = commands[cmdIdx];
  const label = cmdIdx.toString();
  conn.exec(cmd, (err, stream) => {
    if (err) { results[label] = { cmd, stdout: '', stderr: 'ERROR: ' + err.message }; cmdIdx++; runNext(); return; }
    let stdout = '', stderr = '';
    stream.on('data', d => stdout += d.toString());
    stream.stderr.on('data', d => stderr += d.toString());
    stream.on('close', () => { results[label] = { cmd, stdout, stderr }; cmdIdx++; runNext(); });
  });
}
conn.connect({ host: '5.223.81.16', username: 'root', privateKey: key, readyTimeout: 10000 });
conn.on('error', (err) => { console.error('SSH ERROR:', err.message); process.exit(1); });
