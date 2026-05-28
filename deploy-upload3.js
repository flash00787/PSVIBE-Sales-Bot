const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const PRIVATE_KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
const TARGET = '/root/Sales-Tele-Bot_refactored';
const BACKUP = '/root/backups';

function execCmd(conn, cmd, label) {
  return new Promise((resolve, reject) => {
    console.log(`\n[${label}] Running...`);
    conn.exec(cmd, (err, stream) => {
      if (err) { console.error(`[${label}] error:`, err); reject(err); return; }
      let stdout = '', stderr = '';
      stream.on('data', d => { stdout += d.toString(); process.stdout.write(d); });
      stream.stderr.on('data', d => { stderr += d.toString(); process.stderr.write('E: '+d); });
      stream.on('close', code => {
        console.log(`\n[${label}] exit=${code}`);
        if (code === 0) resolve({stdout, stderr});
        else reject(new Error(`${label} failed with code ${code}: ${stderr}`));
      });
    });
  });
}

async function main() {
  // 1. Decode backup
  console.log('Decoding backup...');
  const raw = fs.readFileSync('/home/node/.openclaw/workspace/2026-05-26_refactored_backup.b64', 'utf-8');
  const idx = raw.indexOf('H4sI');
  const decoded = Buffer.from(raw.slice(idx), 'base64');
  if (decoded[0] !== 0x1f || decoded[1] !== 0x8b) { console.error('Not gzip!'); return; }
  const TAR = '/tmp/bot.tar.gz';
  fs.writeFileSync(TAR, decoded);
  console.log(`Decoded ${decoded.length} bytes`);

  const conn = new Client();

  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({ host: HOST, port: 22, username: 'root', privateKey: PRIVATE_KEY, readyTimeout: 30000 });
  });
  console.log('SSH connected');

  // 2. Create directories
  await execCmd(conn, `mkdir -p ${BACKUP} ${TARGET} && echo "dirs ok"`, 'mkdir');

  // 3. Upload tar.gz via SFTP
  console.log('\n[SFTP] Uploading...');
  await new Promise((resolve, reject) => {
    conn.sftp((err, sftp) => {
      if (err) { reject(err); return; }
      const r = fs.createReadStream(TAR);
      const w = sftp.createWriteStream(`${BACKUP}/bot.tar.gz`);
      w.on('close', () => { console.log('[SFTP] done'); resolve(); });
      w.on('error', reject);
      r.pipe(w);
    });
  });

  // 4. Extract
  await execCmd(conn, `cd ${TARGET} && tar xzf ${BACKUP}/bot.tar.gz && echo "extracted" && ls -la ${TARGET}/`, 'extract');

  // 5. Check - files might be in a subdir
  await execCmd(conn, `find ${TARGET} -maxdepth 3 -name 'main.py' -type f`, 'find-main');

  // 6. Figure out actual working dir (tar might have top-level dir)
  const { stdout } = await execCmd(conn, `
if [ -f "${TARGET}/main.py" ]; then
  echo "WD=${TARGET}"
elif [ -f "${TARGET}/Sales-Tele-Bot_refactored/main.py" ]; then
  echo "WD=${TARGET}/Sales-Tele-Bot_refactored"
  echo "NEED_MOVE=yes"
else
  echo "ERROR: cannot find main.py"
  find ${TARGET} -name 'main.py' -type f
fi
`, 'locate-wd');

  console.log('Locate result:', stdout);

  conn.end();
  console.log('\nDone.');
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
