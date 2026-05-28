const {Client} = require('ssh2');
const conn = new Client();
conn.on('ready', () => {
  conn.exec(
    `docker exec psvibe-mysql mysql -uroot -pPsVibe@MySQL2024! psvibe_api -e "SELECT * FROM sync_status; SELECT COUNT(*) as member_count FROM member_wallets; SELECT COUNT(*) as game_count FROM games_library; SELECT COUNT(*) as staff_count FROM staff_records; SELECT COUNT(*) as console_count FROM console_status;" 2>&1`,
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
