#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');
const HOST = '5.223.81.16';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

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

function sshPut(local, remote) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn.on('ready', () => {
      conn.sftp((err, sftp) => {
        if (err) { conn.end(); reject(err); return; }
        sftp.fastPut(local, remote, err => {
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
  console.log('Uploading fix script...');
  await sshPut('/home/node/.openclaw/workspace/temp/fix_remaining.py', '/root/fix_remaining.py');
  
  console.log('Running fixes...\n');
  let r = await sshExec('python3 /root/fix_remaining.py');
  console.log(r.stdout);
  if (r.stderr) console.error('STDERR:', r.stderr);
  
  console.log('\n=== Running Quality Gate ===\n');
  r = await sshExec('cd /root/psvibe-sales-bot && python3 /root/coordination/quality_gate.py --quick 2>&1', 120000);
  console.log(r.stdout);
  
  await sshExec('rm -f /root/fix_remaining.py');
  console.log('Complete.');
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
