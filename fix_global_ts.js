const fs = require('fs');
const { Client } = require('ssh2');
const sshKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

const conn = new Client();

conn.on('ready', () => {
  conn.exec('grep -n "global _MBR_TS" /root/psvibe-sales-bot/bot/__init__.py', (err, stream) => {
    if (err) throw err;
    let data = '';
    stream.on('data', (chunk) => { data += chunk; });
    stream.stderr.on('data', (chunk) => { process.stderr.write(chunk); });
    stream.on('close', () => {
      console.log('=== ALL global _MBR_TS occurrences ===');
      console.log(data);
      
      conn.exec('sed -n "2085,2130p" /root/psvibe-sales-bot/bot/__init__.py', (err2, stream2) => {
        if (err2) throw err2;
        let d2 = '';
        stream2.on('data', (chunk) => { d2 += chunk; });
        stream2.stderr.on('data', (chunk) => { process.stderr.write(chunk); });
        stream2.on('close', () => {
          console.log('\n=== save_referral_code function (lines 2085-2130) ===');
          console.log(d2);
          
          conn.exec('sed -n "1830,1850p" /root/psvibe-sales-bot/bot/__init__.py', (err3, stream3) => {
            if (err3) throw err3;
            let d3 = '';
            stream3.on('data', (chunk) => { d3 += chunk; });
            stream3.stderr.on('data', (chunk) => { process.stderr.write(chunk); });
            stream3.on('close', () => {
              console.log('\n=== _load_members function area (lines 1830-1850) ===');
              console.log(d3);
              
              conn.exec('sed -n "2150,2180p" /root/psvibe-sales-bot/bot/__init__.py', (err4, stream4) => {
                if (err4) throw err4;
                let d4 = '';
                stream4.on('data', (chunk) => { d4 += chunk; });
                stream4.stderr.on('data', (chunk) => { process.stderr.write(chunk); });
                stream4.on('close', () => {
                  console.log('\n=== Other function area (lines 2150-2180) ===');
                  console.log(d4);
                  conn.end();
                });
              });
            });
          });
        });
      });
    });
  });
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: sshKey
});
