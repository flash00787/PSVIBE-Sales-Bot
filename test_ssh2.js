#!/usr/bin/env node
const { Client } = require('ssh2');

const HOST = '167.71.196.120';
const USER = 'root';
const PASS = 'Freedom2024#Revflash';

console.log('Test 3: Password with all algorithms enabled...');
const c3 = new Client();
c3.on('ready', () => {
  console.log('✅ SUCCESS with all algorithms!');
  c3.exec('hostname && whoami && ls /root/', (err, stream) => {
    if (err) { console.log('Exec error:', err); c3.end(); return; }
    stream.on('data', d => console.log('Output:', d.toString()));
    stream.stderr.on('data', d => console.log('Stderr:', d.toString()));
    stream.on('close', () => { console.log('Done'); c3.end(); });
  });
});
c3.on('error', (err) => {
  console.log('❌ Failed:', err.message);
  c3.end();
  process.exit(1);
});
c3.connect({
  host: HOST,
  port: 22,
  username: USER,
  password: PASS,
  readyTimeout: 15000,
  algorithms: {
    kex: [
      'diffie-hellman-group1-sha1',
      'diffie-hellman-group14-sha1',
      'diffie-hellman-group14-sha256',
      'diffie-hellman-group16-sha512',
      'diffie-hellman-group18-sha512',
      'diffie-hellman-group-exchange-sha1',
      'diffie-hellman-group-exchange-sha256',
      'ecdh-sha2-nistp256',
      'ecdh-sha2-nistp384',
      'ecdh-sha2-nistp521',
      'curve25519-sha256',
      'curve25519-sha256@libssh.org',
    ],
    cipher: [
      'aes128-ctr',
      'aes192-ctr',
      'aes256-ctr',
      'aes128-gcm@openssh.com',
      'aes256-gcm@openssh.com',
      'aes256-cbc',
      'aes192-cbc',
      'aes128-cbc',
      '3des-cbc',
    ],
    serverHostKey: [
      'ssh-rsa',
      'ssh-dss',
      'ecdsa-sha2-nistp256',
      'ecdsa-sha2-nistp384',
      'ecdsa-sha2-nistp521',
      'ssh-ed25519',
    ],
    hmac: [
      'hmac-sha2-256',
      'hmac-sha2-512',
      'hmac-sha1',
      'hmac-md5',
    ],
  },
});
