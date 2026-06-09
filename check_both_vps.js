#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const MAIN_KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

async function sshExec(client, cmd, timeout = 30000) {
  return new Promise((resolve, reject) => {
    client.exec(cmd, { timeout }, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', (d) => { stdout += d.toString(); });
      stream.stderr.on('data', (d) => { stderr += d.toString(); });
      stream.on('close', (code) => resolve({ code, stdout: stdout.trim(), stderr: stderr.trim() }));
    });
  });
}

function sshConnect(config) {
  return new Promise((resolve, reject) => {
    const client = new Client();
    client.on('ready', () => resolve(client));
    client.on('error', reject);
    client.connect(config);
  });
}

async function main() {
  // 1. Test key auth to source VPS
  console.log('=== Testing Key Auth to Source VPS (167.71.196.120) ===');
  try {
    const src = await sshConnect({
      host: '167.71.196.120', port: 22, username: 'root',
      privateKey: MAIN_KEY, readyTimeout: 10000,
    });
    console.log('✅ Key auth works on Source VPS!');
    let r = await sshExec(src, 'hostname && ls /root/ | grep -i wallet');
    console.log('Hostname:', r.stdout.split('\n')[0]);
    console.log('Wallet dirs:', r.stdout.split('\n').slice(1).join(', ') || '(none)');
    r = await sshExec(src, 'ls /root/ | head -40');
    console.log('/root contents:', r.stdout);
    src.end();
  } catch(e) {
    console.log('❌ Key auth failed on Source VPS:', e.message);
  }

  // 2. Check Main VPS
  console.log('\n=== Checking Main VPS (5.223.81.16) ===');
  try {
    const main = await sshConnect({
      host: '5.223.81.16', port: 22, username: 'root',
      privateKey: MAIN_KEY, readyTimeout: 10000,
    });
    console.log('✅ Connected to Main VPS!');
    let r = await sshExec(main, 'hostname');
    console.log('Hostname:', r.stdout);
    
    r = await sshExec(main, 'ls /root/ | grep -i wallet');
    console.log('Wallet dirs:', r.stdout || '(none)');
    
    r = await sshExec(main, 'ls /root/ | head -40');
    console.log('/root contents:', r.stdout);

    r = await sshExec(main, 'ls /root/YYO-Personal-Wallet 2>&1');
    console.log('YYO-Personal-Wallet exists?', r.stdout.includes('cannot access') ? 'NO' : 'YES');
    
    // Check for any existing wallet services
    r = await sshExec(main, 'systemctl list-units --type=service --all | grep -i wallet');
    console.log('Wallet services:', r.stdout || '(none)');
    
    // Check docker/OpenClaw/Nova
    r = await sshExec(main, 'docker ps --format "{{.Names}} {{.Image}} {{.Status}}" 2>&1');
    console.log('Docker containers:', r.stdout || '(none)');
    
    r = await sshExec(main, 'find /root /home /opt -maxdepth 3 -name "openclaw.json" 2>/dev/null');
    console.log('OpenClaw configs:', r.stdout || '(none)');
    
    r = await sshExec(main, 'ls /root/openclaw 2>&1; ls /opt/openclaw 2>&1; ls /home/node 2>&1');
    console.log('OpenClaw dirs:', r.stdout || '(none)');
    
    main.end();
  } catch(e) {
    console.log('❌ Main VPS connection failed:', e.message);
  }

  // 3. Try key auth only to source VPS 
  console.log('\n=== Testing Source VPS with key + password fallback ===');
  try {
    const src2 = await sshConnect({
      host: '167.71.196.120', port: 22, username: 'root',
      privateKey: MAIN_KEY,
      password: 'Freedom2024#Revflash',
      readyTimeout: 10000,
    });
    console.log('✅ Source VPS connected (key or password worked)');
    let r = await sshExec(src2, 'hostname && whoami');
    console.log('Connected as:', r.stdout);
    src2.end();
  } catch(e) {
    console.log('❌ Both key and password failed:', e.message);
  }
}

main().catch(console.error);
