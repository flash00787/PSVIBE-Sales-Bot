const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const PRIVATE_KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
const TARGET = '/root/Sales-Tele-Bot_refactored';
const BACKUP = '/root/backups';

async function main() {
  // Decode backup
  console.log('Decoding backup...');
  const raw = fs.readFileSync('/home/node/.openclaw/workspace/2026-05-26_refactored_backup.b64', 'utf-8');
  const decoded = Buffer.from(raw.slice(raw.indexOf('H4sI')), 'base64');
  if (decoded[0] !== 0x1f || decoded[1] !== 0x8b) throw new Error('Not gzip');
  const TAR = '/tmp/bot.tar.gz';
  fs.writeFileSync(TAR, decoded);
  console.log(`Decoded ${decoded.length} bytes`);

  const conn = new Client();
  await new Promise((res, rej) => {
    conn.on('ready', res);
    conn.on('error', rej);
    conn.connect({ host: HOST, port: 22, username: 'root', privateKey: PRIVATE_KEY, readyTimeout: 30000 });
  });
  console.log('SSH connected');

  // Helper
  const exec = (cmd) => new Promise((res, rej) => {
    console.log(`\n>>> ${cmd.slice(0, 80)}...`);
    conn.exec(cmd, (err, stream) => {
      if (err) { rej(err); return; }
      let out = '';
      stream.on('data', d => { out += d.toString(); process.stdout.write(d.toString()); });
      stream.stderr.on('data', d => { process.stderr.write('E:'+d); out += d.toString(); });
      stream.on('close', code => {
        if (code === 0) res(out);
        else rej(new Error(`exit ${code}`));
      });
    });
  });

  // 1. Prepare dirs
  await exec(`rm -rf ${TARGET} && mkdir -p ${TARGET} ${BACKUP}`);

  // 2. Upload
  console.log('\n[SFTP] Uploading...');
  await new Promise((res, rej) => {
    conn.sftp((err, sftp) => {
      if (err) { rej(err); return; }
      fs.createReadStream(TAR).pipe(sftp.createWriteStream(`${BACKUP}/bot.tar.gz`))
        .on('close', res).on('error', rej);
    });
  });
  console.log('[SFTP] done');

  // 3. Extract (tar has Sales-Tele-Bot_refactored/ prefix, extract one level up then move)
  await exec(`cd /root && tar xzf ${BACKUP}/bot.tar.gz && echo "extracted"`);

  // 4. Check structure
  await exec(`ls -la ${TARGET}/`);
  await exec(`ls -la /root/Sales-Tele-Bot_refactored/Sales-Tele-Bot_refactored/ 2>&1 || true`);

  // 5. If double-nested, flatten
  await exec(`
if [ -d "${TARGET}/Sales-Tele-Bot_refactored" ]; then
  echo "Flattening nested dir..."
  cp -r ${TARGET}/Sales-Tele-Bot_refactored/* ${TARGET}/
  echo "done"
fi
ls -la ${TARGET}/
`);

  // 6. Copy .env
  await exec(`cp /root/Sales-Tele-Bot/.env ${TARGET}/.env && echo ".env copied"`);

  // 7. Find main.py and check imports
  await exec(`ls -la ${TARGET}/main.py && echo "---" && head -40 ${TARGET}/main.py`);
  await exec(`ls ${TARGET}/bot/ ${TARGET}/handlers/ 2>&1 | head -20`);
  await exec(`find ${TARGET} -name 'requirements.txt' -type f -o -name 'setup.py' -type f`);

  conn.end();
  console.log('\n=== Phase 1 complete ===');
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
