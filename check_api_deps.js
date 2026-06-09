const {Client} = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  conn.exec(`ls /root/psvibe_api_server/venv/lib/python3.*/site-packages/ | grep -iE "mysql|pymysql|connector" 2>&1 && echo '===REQ===' && cat /root/psvibe_api_server/requirements.txt 2>&1 && echo '===SHEETSCLIENT===' && cat /root/psvibe_api_server/sheets_client.py 2>&1`, (err, stream) => {
    if (err) { console.log('ERR:', err.message); conn.end(); return; }
    let out='';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => { 
      fs.writeFileSync('/home/node/.openclaw/workspace/api_server_deps.txt', out);
      console.log('Saved');
      conn.end(); 
    });
  });
}).connect({ host:'5.223.81.16', port:22, username:'root', privateKey: require('fs').readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
