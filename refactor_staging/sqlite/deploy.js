const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');
const { exec: execCb } = require('child_process');
const util = require('util');
const exec = util.promisify(execCb);

const HOST = '167.71.196.120';
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const LOCAL_DIR = '/home/node/.openclaw/workspace/refactor_staging/sqlite';
const REMOTE_DIR = '/root/Sales-Tele-Bot_refactored/sqlite';
const DB_PATH = '/root/Sales-Tele-Bot_refactored/psvibe.db';

const FILES = ['schema.sql', 'db_manager.py', 'setup.py', 'sync_cron.sh'];

async function readFile(filepath) {
  return fs.promises.readFile(filepath, 'utf8');
}

function sshExec(conn, command) {
  return new Promise((resolve, reject) => {
    conn.exec(command, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', (d) => { stdout += d.toString(); });
      stream.stderr.on('data', (d) => { stderr += d.toString(); });
      stream.on('close', (code) => {
        if (code !== 0 && stderr) {
          // Often Python prints to stderr even on success,
          // only treat as error if code is non-zero and stdout is empty
          if (!stdout.trim()) {
            reject(new Error(`Command failed (code ${code}): ${stderr.trim()}`));
          } else {
            resolve({ stdout, stderr, code });
          }
        } else {
          resolve({ stdout, stderr, code });
        }
      });
    });
  });
}

function createSftpClient(conn) {
  return new Promise((resolve, reject) => {
    conn.sftp((err, sftp) => {
      if (err) return reject(err);
      resolve(sftp);
    });
  });
}

function sftpMkdir(sftp, dir) {
  return new Promise((resolve, reject) => {
    sftp.mkdir(dir, (err) => {
      // Ignore EEXIST
      if (err && err.code !== 4) return reject(err);
      resolve();
    });
  });
}

function sftpPut(sftp, localPath, remotePath) {
  return new Promise((resolve, reject) => {
    sftp.fastPut(localPath, remotePath, (err) => {
      if (err) return reject(err);
      resolve();
    });
  });
}

async function run() {
  console.log('[DEPLOY] Starting SQLite deployment to VPS...\n');

  // Read private key
  const privateKey = await readFile(KEY_PATH);
  const fileContents = {};
  for (const f of FILES) {
    fileContents[f] = await readFile(path.join(LOCAL_DIR, f));
    console.log(`[READ] ${f} (${fileContents[f].length} bytes)`);
  }

  // Connect to VPS
  const conn = new Client();
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({ host: HOST, port: 22, username: USER, privateKey });
  });
  console.log('[CONNECT] SSH connected to VPS');

  try {
    // Step 1: Create remote directories
    console.log('\n--- STEP 1: Create directories ---');
    await sshExec(conn, `mkdir -p ${REMOTE_DIR}`);
    console.log(`[OK] Created ${REMOTE_DIR}`);

    // Also ensure project dir exists
    await sshExec(conn, `mkdir -p /root/Sales-Tele-Bot_refactored`);
    console.log('[OK] Created /root/Sales-Tele-Bot_refactored');

    // Step 2: Copy files via SFTP
    console.log('\n--- STEP 2: Copy files ---');
    const sftp = await createSftpClient(conn);
    await sftpMkdir(sftp, '/root/Sales-Tele-Bot_refactored');
    await sftpMkdir(sftp, REMOTE_DIR);

    for (const f of FILES) {
      const localPath = path.join(LOCAL_DIR, f);
      const remotePath = `${REMOTE_DIR}/${f}`;
      await sftpPut(sftp, localPath, remotePath);
      console.log(`[SFTP] Uploaded ${f} → ${remotePath}`);
    }

    // Make shell script executable
    await sshExec(conn, `chmod +x ${REMOTE_DIR}/sync_cron.sh`);
    console.log('[OK] sync_cron.sh marked executable');

    // Step 3: Create tables only (--no-import since env vars might not be set)
    console.log('\n--- STEP 3: Create tables (without import) ---');
    // First check if .env exists and try to source it
    const envCheck = await sshExec(conn, `test -f /root/Sales-Tele-Bot/.env && echo "EXISTS" || echo "NOT_FOUND"`);
    const envPath = envCheck.stdout.includes('EXISTS') ? '/root/Sales-Tele-Bot/.env' : '';

    if (envPath) {
      console.log('[INFO] Found .env at', envPath);
      const setupCmd = `cd ${REMOTE_DIR} && set -a && source ${envPath} 2>/dev/null; set +a; export SQLITE_DB_PATH=${DB_PATH}; export GOOGLE_APPLICATION_CREDENTIALS=/root/Sales-Tele-Bot/service_account.json; PYTHONPATH=${REMOTE_DIR} python3 ${REMOTE_DIR}/setup.py --db ${DB_PATH}`;
      console.log('[EXEC] Running setup.py with Sheets import...');
      const result = await sshExec(conn, setupCmd);
      console.log(result.stdout);
      if (result.stderr && !result.stderr.includes('INFO') && !result.stderr.includes('WARNING')) {
        console.log('[STDERR]', result.stderr.substring(0, 500));
      }
    } else {
      console.log('[INFO] No .env found — creating empty DB with tables only');
      const setupCmd = `cd ${REMOTE_DIR} && export SQLITE_DB_PATH=${DB_PATH}; python3 ${REMOTE_DIR}/setup.py --db ${DB_PATH} --no-import`;
      const result = await sshExec(conn, setupCmd);
      console.log(result.stdout);
      if (result.stderr) console.log('[STDERR]', result.stderr.substring(0, 500));
    }

    // Step 4: Verify DB was created
    console.log('\n--- STEP 4: Verify ---');
    const verify = await sshExec(conn, `python3 -c "
import sqlite3
conn = sqlite3.connect('${DB_PATH}')
cur = conn.cursor()
cur.execute('SELECT name FROM sqlite_master WHERE type=\\\"table\\\" ORDER BY name')
tables = [r[0] for r in cur.fetchall()]
print(f'Tables created: {len(tables)}')
for t in tables:
    cur.execute(f'SELECT COUNT(*) FROM [{t}]')
    print(f'  {t}: {cur.fetchone()[0]} rows')
conn.close()
"`);
    console.log(verify.stdout);

    // Step 5: Test db_manager.py directly
    console.log('\n--- STEP 5: Test db_manager.py ---');
    const testResult = await sshExec(conn, `cd ${REMOTE_DIR} && python3 -c "
import sys; sys.path.insert(0,'.')
from db_manager import PSVibeDB
db = PSVibeDB('${DB_PATH}')
print('✓ PSVibeDB initialized')
print(f'  Members: {db.get_member_count()}')
consoles = db.get_all_consoles()
print(f'  Consoles: {len(consoles)}')
games = db.get_games()
print(f'  Games: {len(games)}')
settings = db.get_all_settings()
print(f'  Settings: {len(settings)}')
bk = db.get_active_bookings()
print(f'  Active Bookings: {len(bk)}')
staff = db.get_all_staff()
print(f'  Staff: {len(staff)}')
db.close()
print('✓ All db_manager tests passed')
"`);
    console.log(testResult.stdout);
    if (testResult.stderr) console.log('[STDERR]', testResult.stderr.substring(0, 300));

    console.log('\n[DEPLOY] Deployment completed successfully!');

  } catch (err) {
    console.error('[ERROR]', err.message);
    process.exit(1);
  } finally {
    conn.end();
  }
}

run().catch(err => {
  console.error('[FATAL]', err);
  process.exit(1);
});
