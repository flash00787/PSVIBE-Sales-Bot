const { Client } = require('ssh2');

const conn = new Client();
conn.on('ready', () => {
  // Fix: change "return result" to extract the data array
  conn.exec('sed -n \"1729,1731p\" /root/psvibe-sale-bot/bot/__init__.py', (err, stream) => {
    let out = '';
    stream.on('data', d => out += d);
    stream.on('close', () => {
      console.log('BEFORE FIX:');
      console.log(out);
      
      // Apply the fix
      const fixCmd = `sed -i '1730s/return result/return set(result.get("data", []))/' /root/psvibe-sale-bot/bot/__init__.py`;
      conn.exec(fixCmd, (err2, stream2) => {
        let out2 = '';
        stream2.on('data', d => out2 += d);
        stream2.on('close', () => {
          // Verify
          conn.exec('sed -n \"1729,1731p\" /root/psvibe-sale-bot/bot/__init__.py', (err3, stream3) => {
            let out3 = '';
            stream3.on('data', d => out3 += d);
            stream3.on('close', () => {
              console.log('AFTER FIX:');
              console.log(out3);
              conn.end();
            });
          });
        });
      });
    });
  });
});
conn.connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: require('fs').readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
