const { Client } = require('ssh2');
const { readFileSync, writeFileSync, createWriteStream, existsSync, mkdirSync } = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

async function runSSH(cmd) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { conn.end(); return reject(err); }
        let stdout = '', stderr = '';
        stream.on('data', d => stdout += d.toString());
        stream.stderr.on('data', d => stderr += d.toString());
        stream.on('close', (code) => {
          conn.end();
          resolve({ code, stdout, stderr });
        });
      });
    });
    conn.connect({ host: HOST, username: USER, privateKey: readFileSync(KEY_PATH) });
  });
}

async function main() {
  const action = process.argv[2] || 'status';

  if (action === 'status') {
    // Check current V1 state
    const r1 = await runSSH('ls -la /root/Sales-Tele-Bot/main.py && echo "---LINES---" && wc -l /root/Sales-Tele-Bot/main.py && echo "---STATUS---" && systemctl is-active psvibe-bot.service && echo "---PID---" && systemctl show -p MainPID psvibe-bot.service');
    console.log('=== V1 STATUS ===');
    console.log(r1.stdout);
    if (r1.stderr) console.error('STDERR:', r1.stderr);

    // Check existing backups
    const r2 = await runSSH('echo "=== BACKUPS ===" && ls -lh /root/backups/ 2>/dev/null');
    console.log(r2.stdout);

    // Check V2 status
    const r3 = await runSSH('echo "=== V2 DIRECTORY ===" && ls -la /root/Sales-Tele-Bot_refactored/ 2>/dev/null | head -5 && echo "---DEPLOY SCRIPT---" && test -f /root/staging/scripts/deploy.sh && echo "deploy.sh exists" || echo "no deploy.sh"');
    console.log(r3.stdout);
    
    // Check backup inventory
    const r4 = await runSSH('echo "=== BACKUPS V1 ===" && ls -lh /root/backups/*v1* /root/backups/*monolithic* /root/backups/*original* 2>/dev/null');
    console.log(r4.stdout);

  } else if (action === 'backup') {
    const ts = new Date().toISOString().replace(/[:.]/g,'-').slice(0,19);
    const BACKUP_DIR = `/root/backups`;
    const BACKUP_FILE = `v1-monolithic-${ts}.tar.gz`;
    
    // Create backup directory
    await runSSH(`mkdir -p ${BACKUP_DIR}`);
    
    // Create tar backup of V1
    console.log(`📦 Creating backup: ${BACKUP_FILE} ...`);
    const r1 = await runSSH(`cd /root && tar czf ${BACKUP_DIR}/${BACKUP_FILE} --exclude='node_modules' --exclude='__pycache__' Sales-Tele-Bot/ 2>&1 && echo "OK" || echo "FAILED"`);
    console.log('Backup result:', r1.stdout);
    if (r1.stderr) console.error('STDERR:', r1.stderr);

    const r2 = await runSSH(`ls -lh ${BACKUP_DIR}/${BACKUP_FILE} && md5sum ${BACKUP_DIR}/${BACKUP_FILE}`);
    console.log('Backup file:', r2.stdout);

    console.log(`\n✅ Backup saved: ${BACKUP_DIR}/${BACKUP_FILE}`);

  } else if (action === 'delete') {
    console.log('⚠️  STOPPING psvibe-bot.service and DELETING V1 from /root/Sales-Tele-Bot/ ...');
    
    // Stop the service first
    const r1 = await runSSH(`systemctl stop psvibe-bot.service && systemctl is-active psvibe-bot.service`);
    console.log('Service stop:', r1.stdout);
    if (r1.stderr) console.error('STDERR:', r1.stderr);

    // Backup first (just in case from the last backup step)
    // Then delete
    const r2 = await runSSH(`rm -rf /root/Sales-Tele-Bot/main.py /root/Sales-Tele-Bot/handlers/ /root/Sales-Tele-Bot/utils/ /root/Sales-Tele-Bot/config/ 2>&1; rm -rf /root/Sales-Tele-Bot/*.py /root/Sales-Tele-Bot/*.json /root/Sales-Tele-Bot/*.txt /root/Sales-Tele-Bot/*.sh 2>/dev/null; echo "---REMAINING---"; ls /root/Sales-Tele-Bot/ 2>/dev/null || echo "EMPTY/DELETED"`);
    console.log('Delete result:', r2.stdout);
    if (r2.stderr) console.error('STDERR:', r2.stderr);

    // Verify deletion
    const r3 = await runSSH(`test -f /root/Sales-Tele-Bot/main.py && echo "⚠️ main.py still exists!" || echo "✅ main.py deleted"`);
    console.log(r3.stdout);

  } else if (action === 'backup_delete') {
    // Combined: Backup, then stop service, then delete
    const ts = new Date().toISOString().replace(/[:.]/g,'-').slice(0,19);
    const BACKUP_DIR = `/root/backups`;
    const BACKUP_FILE = `v1-monolithic-final-${ts}.tar.gz`;
    
    console.log('📦 Step 1: Creating final backup...');
    await runSSH(`mkdir -p ${BACKUP_DIR}`);
    
    const r1 = await runSSH(`cd /root && tar czf ${BACKUP_DIR}/${BACKUP_FILE} --exclude='node_modules' --exclude='__pycache__' Sales-Tele-Bot/ 2>&1 && echo "OK" || echo "FAILED"`);
    console.log('Backup:', r1.stdout);
    
    const r2 = await runSSH(`ls -lh ${BACKUP_DIR}/${BACKUP_FILE}`);
    console.log('Backup file:', r2.stdout);
    
    console.log('🛑 Step 2: Stopping V1 service...');
    const r3 = await runSSH(`systemctl stop psvibe-bot.service`);
    console.log('Service stopped:', r3.stdout);
    
    console.log('🗑️ Step 3: Deleting V1 from /root/Sales-Tele-Bot/ ...');
    const r4 = await runSSH(`rm -rf /root/Sales-Tele-Bot/ 2>&1 && echo "✅ Deleted" || echo "❌ Failed"`);
    console.log(r4.stdout);
    
    const r5 = await runSSH(`test -d /root/Sales-Tele-Bot && echo "⚠️ DIR still exists" || echo "✅ Directory removed"`);
    console.log(r5.stdout);
    
    // Verify backup exists
    const r6 = await runSSH(`ls -lh ${BACKUP_DIR}/${BACKUP_FILE}`);
    console.log('\n📋 Final verification:');
    console.log(`Backup: ${BACKUP_DIR}/${BACKUP_FILE} (${r6.stdout.trim()})`);
  }

  process.exit(0);
}

main().catch(err => { console.error('FATAL:', err); process.exit(1); });
