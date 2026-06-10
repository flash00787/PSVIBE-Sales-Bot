#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
const BASE = '/home/node/.openclaw/workspace/temp';

function sshExec(cmd, timeout = 60000) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.exec(cmd, { timeout }, (err, stream) => {
        if (err) { conn.end(); reject(err); return; }
        let out = '', errOut = '';
        stream.on('data', d => { out += d.toString(); });
        stream.stderr.on('data', d => { errOut += d.toString(); });
        stream.on('close', code => {
          conn.end();
          resolve({ stdout: out, stderr: errOut, code });
        });
      });
    });
    conn.on('error', reject);
    conn.connect({ host: HOST, username: 'root', privateKey: KEY, readyTimeout: 15000 });
  });
}

function sshPut(localFile, remotePath) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.sftp((err, sftp) => {
        if (err) { conn.end(); reject(err); return; }
        sftp.fastPut(localFile, remotePath, err => {
          conn.end();
          if (err) reject(err);
          else resolve();
        });
      });
    });
    conn.on('error', reject);
    conn.connect({ host: HOST, username: 'root', privateKey: KEY, readyTimeout: 15000 });
  });
}

async function main() {
  // Upload fix scripts
  console.log('Uploading fix scripts...');
  await sshPut(`${BASE}/fix_setup.py`, '/root/fix_setup.py');
  await sshPut(`${BASE}/fix_topup_prints.py`, '/root/fix_topup_prints.py');
  await sshPut(`${BASE}/fix_alerts.sh`, '/root/fix_alerts.sh');
  console.log('Uploads complete.\n');

  // STEP 1: Fix bare excepts
  console.log('=== STEP 1: Fix bare excepts ===');
  let r = await sshExec('python3 /root/fix_setup.py');
  console.log(r.stdout);
  if (r.stderr) console.error('STDERR:', r.stderr);

  // Verify compile
  r = await sshExec('python3 -m py_compile /root/psvibe-sales-bot/sqlite/setup.py 2>&1 && echo "COMPILE OK"');
  console.log(r.stdout.trim());

  // STEP 2: Fix print statements
  console.log('\n=== STEP 2: Fix print() in fix_topup_spam.py ===');
  r = await sshExec('python3 /root/fix_topup_prints.py');
  console.log(r.stdout);
  if (r.stderr) console.error('STDERR:', r.stderr);

  // Verify compile
  r = await sshExec('python3 -m py_compile /root/psvibe-sales-bot/fix_topup_spam.py 2>&1 && echo "COMPILE OK"');
  console.log(r.stdout.trim());

  // STEP 3: Resolve alerts
  console.log('\n=== STEP 3: Resolve alerts ===');
  r = await sshExec('bash /root/fix_alerts.sh');
  console.log(r.stdout);

  // STEP 4: Run Quality Gate
  console.log('=== STEP 4: Quality Gate ===');
  r = await sshExec('cd /root/psvibe-sales-bot && python3 /root/coordination/quality_gate.py --quick 2>&1', 120000);
  console.log(r.stdout);
  if (r.stderr) console.error('STDERR:', r.stderr);

  // Cleanup
  await sshExec('rm -f /root/fix_setup.py /root/fix_topup_prints.py /root/fix_alerts.sh');

  console.log('\n=== ALL COMPLETE ===');
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
