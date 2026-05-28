const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const files = process.argv.slice(2);
if (files.length === 0) {
  console.error('Usage: node ssh_read.js <file1> <file2> ...');
  process.exit(1);
}

const conn = new Client();
conn.on('ready', () => {
  let remaining = files.length;
  const results = {};
  
  files.forEach(file => {
    conn.exec(`cat "${file}"`, (err, stream) => {
      if (err) { results[file] = { error: err.message }; if (--remaining === 0) done(); return; }
      let data = '';
      stream.on('data', (chunk) => { data += chunk.toString(); });
      stream.stderr.on('data', (chunk) => { data += chunk.toString(); });
      stream.on('close', (code) => {
        results[file] = { code, data };
        if (--remaining === 0) done();
      });
    });
  });
  
  function done() {
    conn.end();
    console.log(JSON.stringify(results, null, 2));
  }
});

conn.on('error', (err) => {
  console.error('SSH error:', err.message);
  process.exit(1);
});

conn.connect({
  host: '167.71.196.120',
  username: 'root',
  privateKey: fs.readFileSync(path.join(__dirname, '.ssh', 'id_rsa'))
});
