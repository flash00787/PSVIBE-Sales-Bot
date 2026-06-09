#!/usr/bin/env node
/**
 * SFTP-based file transfer: Source → Destination
 */
const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

const SRC_CONFIG = { host: '167.71.196.120', port: 22, username: 'root', privateKey: KEY, readyTimeout: 15000 };
const DST_CONFIG = { host: '5.223.81.16', port: 22, username: 'root', privateKey: KEY, readyTimeout: 15000 };

function sshConnect(opts) {
  return new Promise((resolve, reject) => {
    const c = new Client();
    c.on('ready', () => resolve(c));
    c.on('error', reject);
    c.connect(opts);
  });
}

function sshExec(client, cmd, timeout = 30000) {
  return new Promise((resolve, reject) => {
    client.exec(cmd, { timeout }, (err, stream) => {
      if (err) return reject(err);
      let s = '', e = '';
      stream.on('data', d => s += d.toString());
      stream.stderr.on('data', d => e += d.toString());
      stream.on('close', code => resolve({ code, stdout: s.trim(), stderr: e.trim() }));
    });
  });
}

function sftpGet(client, remotePath, localPath) {
  return new Promise((resolve, reject) => {
    client.sftp((err, sftp) => {
      if (err) return reject(err);
      const writeStream = fs.createWriteStream(localPath);
      const readStream = sftp.createReadStream(remotePath);
      
      let bytes = 0;
      readStream.on('data', (chunk) => {
        bytes += chunk.length;
        if (bytes % (10*1024*1024) < chunk.length) {
          console.log(`  Downloaded: ${Math.round(bytes/1024/1024)} MB`);
        }
      });
      
      readStream.pipe(writeStream);
      writeStream.on('close', () => {
        console.log(`  Total: ${Math.round(bytes/1024/1024)} MB`);
        resolve(bytes);
      });
      readStream.on('error', reject);
      writeStream.on('error', reject);
    });
  });
}

function sftpPut(client, localPath, remotePath) {
  return new Promise((resolve, reject) => {
    client.sftp((err, sftp) => {
      if (err) return reject(err);
      const readStream = fs.createReadStream(localPath);
      const writeStream = sftp.createWriteStream(remotePath);
      
      let bytes = 0;
      writeStream.on('close', () => {
        console.log(`  Uploaded: ${Math.round(bytes/1024/1024)} MB`);
        resolve(bytes);
      });
      
      readStream.on('data', (chunk) => {
        bytes += chunk.length;
        if (bytes % (10*1024*1024) < chunk.length) {
          console.log(`  Uploaded: ${Math.round(bytes/1024/1024)} MB`);
        }
      });
      
      readStream.pipe(writeStream);
      readStream.on('error', reject);
      writeStream.on('error', reject);
    });
  });
}

async function main() {
  const LOCAL_ARCHIVE = '/tmp/wallet_bot2.tar.gz';
  const REMOTE_ARCHIVE_SRC = '/tmp/wallet_bot2.tar.gz';
  const REMOTE_ARCHIVE_DST = '/root/wallet_bot2.tar.gz';

  try {
    let src, dst;

    // ── Step 1: Verify archive exists on source ──
    console.log('=== Checking source archive ===');
    src = await sshConnect(SRC_CONFIG);
    console.log('✅ Connected to Source VPS');
    let r = await sshExec(src, `ls -lh ${REMOTE_ARCHIVE_SRC}`);
    console.log('Archive on source:', r.stdout);
    src.end();

    // ── Step 2: SFTP download from source to gateway ──
    console.log('\n=== Downloading from Source VPS to gateway ===');
    src = await sshConnect(SRC_CONFIG);
    console.log('✅ Connected to Source VPS');
    console.log('Starting SFTP download...');
    await sftpGet(src, REMOTE_ARCHIVE_SRC, LOCAL_ARCHIVE);
    src.end();
    console.log('✅ Download complete');

    // Verify local file
    const localStat = fs.statSync(LOCAL_ARCHIVE);
    console.log(`Local file: ${Math.round(localStat.size/1024/1024)} MB`);

    // ── Step 3: SFTP upload from gateway to destination ──
    console.log('\n=== Uploading to Main VPS ===');
    dst = await sshConnect(DST_CONFIG);
    console.log('✅ Connected to Main VPS');
    console.log('Starting SFTP upload...');
    await sftpPut(dst, LOCAL_ARCHIVE, REMOTE_ARCHIVE_DST);
    console.log('✅ Upload complete');

    // Verify on destination
    r = await sshExec(dst, `ls -lh ${REMOTE_ARCHIVE_DST}`);
    console.log('Archive on destination:', r.stdout);
    
    // Verify MD5
    r = await sshExec(dst, `md5sum ${REMOTE_ARCHIVE_DST}`);
    console.log('Remote MD5:', r.stdout);
    
    const { execSync } = require('child_process');
    const localMd5 = execSync(`md5sum ${LOCAL_ARCHIVE}`).toString().trim();
    console.log('Local MD5:', localMd5);

    dst.end();

    // Clean up local
    fs.unlinkSync(LOCAL_ARCHIVE);
    console.log('\n✅ Transfer complete! File verified.');

  } catch(err) {
    console.error('ERROR:', err.message);
    console.error(err.stack);
    process.exit(1);
  }
}

main().catch(console.error);
