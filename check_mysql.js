const {Client} = require('ssh2');
const conn = new Client();
conn.on('ready', () => {
  conn.exec(
    `docker exec psvibe-mysql mysql -uroot -pPsVibe@MySQL2024! psvibe_api -e "SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY, EXTRA FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='psvibe_api' ORDER BY TABLE_NAME, ORDINAL_POSITION;" 2>&1`,
    (err, stream) => {
      if (err) { console.log('ERR:', err.message); conn.end(); return; }
      let out='';
      stream.on('data', d => out += d.toString());
      stream.stderr.on('data', d => {
        if(!d.toString().includes('Warning')) out += d.toString();
      });
      stream.on('close', () => { console.log(out); conn.end(); });
    }
  );
}).connect({ host:'5.223.81.16', port:22, username:'root', privateKey: require('fs').readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
