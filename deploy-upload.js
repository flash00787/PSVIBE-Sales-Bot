const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const USERNAME = 'root';
const PRIVATE_KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
const TARGET_DIR = '/root/Sales-Tele-Bot_refactored';
const BACKUP_DIR = '/root/backups';

// Decode the base64 file
console.log('Decoding base64 backup...');
const b64 = fs.readFileSync('/home/node/.openclaw/workspace/2026-05-26_refactored_backup.b64', 'utf-8');
const decoded = Buffer.from(b64, 'base64');
const TAR_GZ_PATH = '/tmp/refactored_bot.tar.gz';
fs.writeFileSync(TAR_GZ_PATH, decoded);
console.log(`Decoded: ${decoded.length} bytes -> ${TAR_GZ_PATH}`);

// Check what's in the tar before uploading
const { execSync } = require('child_process');
try {
  const listing = execSync(`tar tzf ${TAR_GZ_PATH} | head -60`, { encoding: 'utf-8' });
  console.log('=== TAR CONTENTS ===');
  console.log(listing);
} catch(e) {
  console.log('tar listing failed:', e.message);
}

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected');

  // Step 1: Create directories and upload
  conn.sftp((err, sftp) => {
    if (err) { console.error('SFTP error:', err); conn.end(); return; }

    const remotePath = '/root/backups/refactored_bot.tar.gz';
    console.log(`Uploading to ${remotePath}...`);

    const readStream = fs.createReadStream(TAR_GZ_PATH);
    const writeStream = sftp.createWriteStream(remotePath);

    writeStream.on('close', () => {
      console.log('Upload complete');

      // Step 2: Run setup commands
      const setupCmds = `
set -e
echo "=== Creating target dir ==="
mkdir -p ${TARGET_DIR}

echo "=== Extracting backup ==="
cd ${TARGET_DIR}
tar xzf ${BACKUP_DIR}/refactored_bot.tar.gz

echo "=== Listing extracted files ==="
ls -la ${TARGET_DIR}/
echo "---"
find ${TARGET_DIR} -maxdepth 2 -type f -name '*.py' | sort
echo "---"
find ${TARGET_DIR} -maxdepth 3 -name 'requirements.txt' -type f

echo "=== Copying .env from old bot ==="
cp /root/Sales-Tele-Bot/.env ${TARGET_DIR}/.env
echo "Copied .env"

echo "=== Checking entry point ==="
for f in main.py app.py run.py bot.py; do
  if [ -f "${TARGET_DIR}/\$f" ]; then
    echo "Found entry point: \${TARGET_DIR}/\$f"
    head -30 "\${TARGET_DIR}/\$f"
    echo "---"
  fi
done
`;

      conn.exec(setupCmds, (err, stream) => {
        if (err) { console.error('Exec error:', err); conn.end(); return; }
        stream.on('data', data => process.stdout.write(data.toString()));
        stream.stderr.on('data', data => process.stderr.write('STDERR: ' + data.toString()));
        stream.on('close', (code) => {
          console.log(`\nSetup exited with code ${code}`);
          conn.end();
        });
      });
    });

    writeStream.on('error', (err) => {
      console.error('Upload error:', err);
      conn.end();
    });

    readStream.pipe(writeStream);
  });
});

conn.on('error', err => { console.error('SSH error:', err); process.exit(1); });

conn.connect({
  host: HOST, port: 22, username: USERNAME,
  privateKey: PRIVATE_KEY,
  readyTimeout: 30000,
});
