#!/usr/bin/env node
const { Client } = require('ssh2');

const HOST = '167.71.196.120';
const USER = 'root';
const PASS = 'Freedom2024#Revflash';

// Test 1: Password auth
console.log('Test 1: Password auth...');
const c1 = new Client();
c1.on('ready', () => {
  console.log('✅ Password auth SUCCESS!');
  c1.exec('hostname && whoami', (err, stream) => {
    if (err) { console.log('Exec error:', err); c1.end(); return; }
    stream.on('data', d => console.log('Output:', d.toString()));
    stream.stderr.on('data', d => console.log('Stderr:', d.toString()));
    stream.on('close', () => c1.end());
  });
});
c1.on('error', (err) => {
  console.log('❌ Password auth failed:', err.message);
  c1.end();
  tryKeyboard();
});
c1.connect({ host: HOST, port: 22, username: USER, password: PASS, readyTimeout: 15000 });

function tryKeyboard() {
  console.log('\nTest 2: Keyboard-interactive auth...');
  const c2 = new Client();
  c2.on('ready', () => {
    console.log('✅ Keyboard-interactive auth SUCCESS!');
    c2.exec('hostname && whoami', (err, stream) => {
      if (err) { console.log('Exec error:', err); c2.end(); return; }
      stream.on('data', d => console.log('Output:', d.toString()));
      stream.stderr.on('data', d => console.log('Stderr:', d.toString()));
      stream.on('close', () => c2.end());
    });
  });
  c2.on('error', (err) => {
    console.log('❌ Keyboard-interactive auth failed:', err.message);
    c2.end();
  });
  c2.on('keyboard-interactive', (name, instructions, lang, prompts, finish) => {
    console.log('Keyboard-interactive prompt:', prompts);
    finish([PASS]);
  });
  c2.connect({
    host: HOST, port: 22, username: USER,
    tryKeyboard: true,
    readyTimeout: 15000,
  });
}
