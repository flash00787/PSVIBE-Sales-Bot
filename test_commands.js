#!/usr/bin/env node
/**
 * Kora Voice Assistant — Test Suite
 * Tests all 10+ command patterns against the live server.
 */

const http = require('http');

const BASE = 'http://localhost:3110';

function post(path, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = http.request(
      BASE + path,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': data.length },
        timeout: 10000,
      },
      (res) => {
        let out = '';
        res.on('data', (d) => (out += d));
        res.on('end', () => {
          try { resolve(JSON.parse(out)); } catch (e) { resolve({ raw: out }); }
        });
      }
    );
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    req.write(data);
    req.end();
  });
}

const TESTS = [
  // Burmese commands
  { name: 'ဒီနေ့ဝင်ငွေ', cmd: 'ဒီနေ့ဝင်ငွေဘယ်လောက်လဲ', expect: 'todaySales' },
  { name: 'ဒီနေ့စာရင်း', cmd: 'PS VIBE ဒီနေ့စာရင်း', expect: 'todayReport' },
  { name: 'ဒီအပတ်စာရင်း', cmd: 'ဒီအပတ်စာရင်းပြပါ', expect: 'weekReport' },
  { name: 'Console status (MM)', cmd: 'console တွေဘယ်လိုရှိလဲ', expect: 'consoleStatus' },
  { name: 'ဒီနေ့လာတဲ့လူ', cmd: 'ဒီနေ့ဘယ်နှစ်ယောက်လာလဲ', expect: 'todayCustomers' },
  { name: 'နာမည်ကြီးဂိမ်း', cmd: 'နာမည်ကြီးဂိမ်းတွေပြပါ', expect: 'topGames' },
  { name: 'ကုန်ခါနီးပစ္စည်း', cmd: 'ကုန်ခါနီးပစ္စည်းရှိလား', expect: 'inventoryLow' },
  { name: 'ဒီနေ့ဝန်ထမ်း', cmd: 'ဒီနေ့ဘယ်သူတွေရှိလဲ', expect: 'staffDuty' },
  { name: 'ဒီနေ့ဘွတ်ကင်', cmd: 'ဒီနေ့ဘွတ်ကင်ဘယ်လောက်ရှိလဲ', expect: 'todayBookings' },
  { name: 'ဘာတွေလုပ်လို့ရလဲ', cmd: 'ဘာတွေလုပ်လို့ရလဲ', expect: 'help' },

  // English commands
  { name: 'today sales', cmd: 'today sales', expect: 'todaySales' },
  { name: 'today income', cmd: 'what is today income', expect: 'todaySales' },
  { name: 'today report', cmd: 'PS VIBE today report', expect: 'todayReport' },
  { name: 'this week report', cmd: 'this week report please', expect: 'weekReport' },
  { name: 'console status', cmd: 'consoles status', expect: 'consoleStatus' },
  { name: 'today customers', cmd: 'how many customers today', expect: 'todayCustomers' },
  { name: 'top games', cmd: 'top games this month', expect: 'topGames' },
  { name: 'inventory low', cmd: 'inventory low stock', expect: 'inventoryLow' },
  { name: 'staff on duty', cmd: 'staff on duty today', expect: 'staffDuty' },
  { name: 'today bookings', cmd: 'today bookings status', expect: 'todayBookings' },
  { name: 'help', cmd: 'help', expect: 'help' },
  { name: 'available commands', cmd: 'what commands are available', expect: 'help' },
];

async function run() {
  console.log('🧪 Kora Voice Assistant — Test Suite\n');
  console.log(`Target: ${BASE}`);
  console.log(`Tests: ${TESTS.length}\n`);

  // Check health first
  try {
    const health = await httpGet('/health');
    console.log(`✅ Health: ${JSON.stringify(health)}\n`);
  } catch (e) {
    console.error(`❌ Server not reachable at ${BASE}`);
    console.error('   Start with: node kora_voice.js');
    process.exit(1);
  }

  let passed = 0;
  let failed = 0;
  const failures = [];

  for (const test of TESTS) {
    try {
      const result = await post('/command', { command: test.cmd });
      const status = result.command === test.expect ? '✅' : '⚠️';
      if (result.command === test.expect) {
        passed++;
      } else {
        failed++;
        failures.push({ ...test, got: result.command });
      }
      console.log(`${status} [${test.name}] → ${result.command} (expected: ${test.expect})`);
    } catch (e) {
      failed++;
      failures.push({ ...test, error: e.message });
      console.log(`❌ [${test.name}] → ERROR: ${e.message}`);
    }
  }

  console.log(`\n${'='.repeat(50)}`);
  console.log(`📊 Results: ${passed} passed, ${failed} failed (${TESTS.length} total)`);

  if (failures.length > 0) {
    console.log(`\n❌ Failures:`);
    failures.forEach((f) => console.log(`   - ${f.name}: expected ${f.expect}, got ${f.got || f.error}`));
  }

  // Test TTS endpoint
  try {
    const tts = await post('/tts', { text: 'Hello PS VIBE' });
    console.log(`\n✅ TTS endpoint: ${JSON.stringify(tts)}`);
  } catch (e) {
    console.log(`\n❌ TTS endpoint failed: ${e.message}`);
  }

  process.exit(failed > 0 ? 1 : 0);
}

function httpGet(path) {
  return new Promise((resolve, reject) => {
    http.get(BASE + path, { timeout: 5000 }, (res) => {
      let out = '';
      res.on('data', (d) => (out += d));
      res.on('end', () => { try { resolve(JSON.parse(out)); } catch (e) { resolve({ raw: out }); } });
    }).on('error', reject);
  });
}

run().catch((e) => {
  console.error(`Fatal: ${e.message}`);
  process.exit(1);
});
