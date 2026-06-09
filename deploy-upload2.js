const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USERNAME = 'root';
const PRIVATE_KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
const TARGET_DIR = '/root/Sales-Tele-Bot_refactored';
const BACKUP_DIR = '/root/backups';

// Decode the base64 file, stripping prefix text
console.log('Decoding base64 backup...');
const raw = fs.readFileSync('/home/node/.openclaw/workspace/2026-05-26_refactored_backup.b64', 'utf-8');
const idx = raw.indexOf('H4sI');
if (idx === -1) { console.error('Cannot find gzip base64 magic'); process.exit(1); }
const cleanB64 = raw.slice(idx);
console.log(`Stripped ${idx} chars prefix`);

const decoded = Buffer.from(cleanB64, 'base64');
console.log(`Decoded: ${decoded.length} bytes`);

// Verify it's gzip
if (decoded[0] !== 0x1f || decoded[1] !== 0x8b) {
  console.error('Not a valid gzip! First bytes:', decoded.slice(0,4).toString('hex'));
  process.exit(1);
}
console.log('Valid gzip confirmed');

const TAR_GZ_PATH = '/tmp/refactored_bot.tar.gz';
fs.writeFileSync(TAR_GZ_PATH, decoded);

// List tar contents
const { execSync } = require('child_process');
try {
  const listing = execSync(`tar tzf ${TAR_GZ_PATH}`, { encoding: 'utf-8', maxBuffer: 10*1024*1024 });
  const lines = listing.trim().split('\n');
  console.log(`=== TAR CONTENTS (${lines.length} files) ===`);
  // Show top-level structure
  const topLevel = new Set();
  lines.forEach(l => {
    const parts = l.split('/');
    if (parts.length >= 1) topLevel.add(parts[0]);
  });
  console.log('Top-level dirs/files:', [...topLevel].join(', '));
  // Show .py files
  const pyFiles = lines.filter(l => l.endsWith('.py'));
  console.log('Python files:', pyFiles.join(', '));
  // Show requirements
  const reqFiles = lines.filter(l => l.endsWith('requirements.txt'));
  console.log('Requirements:', reqFiles.join(', '));
  // Show top-level py files
  const topPy = lines.filter(l => !l.includes('/') && l.endsWith('.py'));
  console.log('Top-level .py:', topPy.join(', ') || 'none');
  // Show first-level dir py files
  const l1py = lines.filter(l => l.split('/').length === 2 && l.endsWith('.py'));
  console.log('Level-1 .py:', l1py.join(', ') || 'none');
} catch(e) {
  console.log('tar listing failed:', e.message);
}

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected');

  // Create backup dir first
  conn.exec(`mkdir -p ${BACKUP_DIR} && mkdir -p ${TARGET_DIR}`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    stream.on('close', () => {
      console.log('Directories created');

      // Now upload via SFTP
      conn.sftp((err, sftp) => {
        if (err) { console.error('SFTP:', err); conn.end(); return; }

        const remotePath = `${BACKUP_DIR}/refactored_bot.tar.gz`;
        console.log(`Uploading to ${remotePath}...`);

        const readStream = fs.createReadStream(TAR_GZ_PATH);
        const writeStream = sftp.createWriteStream(remotePath);

        writeStream.on('close', () => {
          console.log('Upload complete');

          const setupCmds = `
set -e
echo "=== Extracting backup ==="
cd ${TARGET_DIR}
tar xzf ${BACKUP_DIR}/refactored_bot.tar.gz

echo "=== Directory structure ==="
ls -la ${TARGET_DIR}/
find ${TARGET_DIR} -maxdepth 1 -name '*.py' | sort

echo "=== .env from old bot ==="
cp /root/Sales-Tele-Bot/.env ${TARGET_DIR}/.env
ls -la ${TARGET_DIR}/.env

echo "=== Entry point check ==="
for f in main.py app.py run.py bot.py; do
  if [ -f "${TARGET_DIR}/\$f" ]; then
    echo "ENTRY: \${TARGET_DIR}/\$f"
    head -20 "\${TARGET_DIR}/\$f"
  fi
done
`;

          conn.exec(setupCmds, (err, stream) => {
            if (err) { console.error(err); conn.end(); return; }
            stream.on('data', d => process.stdout.write(d.toString()));
            stream.stderr.on('data', d => process.stderr.write('STDERR: ' + d.toString()));
            stream.on('close', code => {
              console.log(`\nSetup exited ${code}`);
              conn.end();
            });
          });
        });

        writeStream.on('error', e => { console.error('Upload err:', e); conn.end(); });
        readStream.pipe(writeStream);
      });
    });
    stream.stderr.on('data', d => process.stderr.write(d.toString()));
  });
});

conn.on('error', err => { console.error('SSH err:', err); process.exit(1); });
conn.connect({ host: HOST, port: 22, username: USERNAME, privateKey: PRIVATE_KEY, readyTimeout: 30000 });
