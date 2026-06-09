const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const files = process.argv.slice(2);
if (!files.length) {
  console.error('Usage: node ssh_read.js <remote-file...>');
  process.exit(1);
}

const conn = new Client();

conn.on('ready', () => {
  let pending = files.length;
  const results = {};
  
  files.forEach((file, idx) => {
    conn.exec(`cat ${file}`, (err, stream) => {
      if (err) { results[file] = `ERROR: ${err.message}`; if (--pending === 0) done(); return; }
      let data = '';
      stream.on('data', (chunk) => { data += chunk; });
      stream.stderr.on('data', (chunk) => { data += chunk; });
      stream.on('close', () => { results[file] = data; if (--pending === 0) done(); });
    });
  });
  
  function done() {
    files.forEach(f => {
      console.log(`=== FILE: ${f} ===`);
      console.log(results[f]);
      console.log(`=== END: ${f} ===\n`);
    });
    conn.end();
  }
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err.message);
  process.exit(1);
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000,
});
