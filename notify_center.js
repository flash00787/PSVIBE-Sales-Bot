#!/usr/bin/env node
/**
 * notify_center.js — Smart Notification Center
 * 
 * Aggregates all system events, alerts, and milestones.
 * Sends smart, non-spammy notifications to Boss.
 * 
 * Usage:
 *   node notify_center.js status      → Show pending notifications
 *   node notify_center.js sales       → Check for sales milestones
 *   node notify_center.js services    → Service status summary
 *   node notify_center.js daily-memo  → Morning digest
 *   node notify_center.js check       → Full notification check
 */

const fs = require('fs');
const path = require('path');
const { Client } = require('ssh2');

const VPS_HOST = '5.223.81.16';
const KEY_PATH = path.join(__dirname, '.ssh', 'id_rsa');
const STATE_PATH = path.join(__dirname, 'memory', 'notify_state.json');

// ── SSH helper ──
function sshExec(cmd, timeout = 10000) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let out = '';
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { conn.end(); reject(err); return; }
        stream.on('data', d => out += d.toString());
        stream.stderr.on('data', d => out += ' STDERR:' + d.toString());
        stream.on('close', () => { conn.end(); resolve(out.trim()); });
      });
    });
    conn.on('error', reject);
    conn.connect({
      host: VPS_HOST, port: 22, username: 'root',
      privateKey: fs.readFileSync(KEY_PATH), readyTimeout: 10000,
    });
    setTimeout(() => { conn.end(); reject(new Error('SSH timeout')); }, timeout);
  });
}

// ── Load state (prevents duplicate alerts) ──
function loadState() {
  try {
    return JSON.parse(fs.readFileSync(STATE_PATH, 'utf8'));
  } catch {
    return {
      lastSalesTotal: 0,
      lastServiceFailures: 0,
      lastCheck: null,
      todaySent: false,
      milestones: { last5M: false, last10M: false },
    };
  }
}

function saveState(state) {
  fs.mkdirSync(path.dirname(STATE_PATH), { recursive: true });
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2));
}

// ── 1. Sales milestone check ──
async function checkSalesMilestones() {
  const state = loadState();
  try {
    const result = await sshExec(
      `mysql -u root -p"PsVibe@MySQL2024!" -h 127.0.0.1 --database=psvibe_api \
       -e "SELECT COALESCE(SUM(amount), 0) as total FROM sales_records WHERE DATE(created_at) = CURDATE();" 2>/dev/null`,
      8000
    );
    const lines = result.split('\n');
    const todayTotal = lines.length > 1 ? parseInt(lines[1]) || 0 : 0;

    let alerts = [];
    
    // Milestone detection
    if (todayTotal >= 100000 && state.milestones.last5M === false) {
      alerts.push(`🎯 **Daily Milestone**: ${todayTotal.toLocaleString()} Ks reached!`);
      state.milestones.last5M = true;
    }
    if (todayTotal >= 500000 && state.milestones.last10M === false) {
      alerts.push(`🔥 **🔥🔥 BIG MILESTONE**: ${todayTotal.toLocaleString()} Ks! Excellent day!`);
      state.milestones.last10M = true;
    }

    // Compare with previous day
    const yesterday = await sshExec(
      `mysql -u root -p"PsVibe@MySQL2024!" -h 127.0.0.1 --database=psvibe_api \
       -e "SELECT COALESCE(SUM(amount), 0) as total FROM sales_records WHERE created_at >= CURDATE() - INTERVAL 1 DAY AND created_at < CURDATE();" 2>/dev/null`,
      5000
    );
    const yLines = yesterday.split('\n');
    const yesterdayTotal = yLines.length > 1 ? parseInt(yLines[1]) || 0 : 0;

    if (yesterdayTotal > 0 && todayTotal >= yesterdayTotal * 1.5) {
      alerts.push(`📈 **Sales up 50%+** from yesterday (${yesterdayTotal.toLocaleString()} → ${todayTotal.toLocaleString()} Ks)`);
    }

    state.lastSalesTotal = todayTotal;
    saveState(state);
    return alerts;
  } catch {
    return [];
  }
}

// ── 2. Service status check ──
async function checkServices() {
  try {
    const result = await sshExec(
      `for s in psvibe-api psvibe-dashboard psvibe-sale-bot psvibe_customer_bot psvibe-watchdog; do echo "$s: $(systemctl is-active $s.service)"; done`,
      10000
    );
    const lines = result.split('\n').filter(l => l.trim());
    const down = lines.filter(l => !l.includes('active'));
    const state = loadState();

    if (down.length > 0 && down.length !== state.lastServiceFailures) {
      state.lastServiceFailures = down.length;
      saveState(state);
      return [`🚨 **Service Alert**: ${down.length} service(s) down!\n` + down.map(l => `  ❌ ${l}`).join('\n')];
    }
    return [];
  } catch {
    return [];
  }
}

// ── 3. Daily morning memo ──
async function dailyMemo() {
  const state = loadState();
  if (state.todaySent) return []; // Only once per day

  const now = new Date();
  const hour = now.getUTCHours() + 6.5; // Myanmar time
  if (hour < 8 || hour > 10) return []; // Only between 8-10 AM

  const dateStr = now.toISOString().split('T')[0];
  
  const memo = [
    `☀️ **Good Morning Boss!** — ${now.toLocaleDateString('en-US', { weekday: 'long', timeZone: 'Asia/Yangon' })}`,
    ``,
    `📋 **Today's Brief:**`,
  ];

  // Check yesterday's sales
  try {
    const result = await sshExec(
      `mysql -u root -p"PsVibe@MySQL2024!" -h 127.0.0.1 --database=psvibe_api \
       -e "SELECT COALESCE(SUM(amount), 0) as total FROM sales_records WHERE created_at >= CURDATE() - INTERVAL 1 DAY AND created_at < CURDATE();" 2>/dev/null`,
      8000
    );
    const lines = result.split('\n');
    const yesterdayTotal = lines.length > 1 ? parseInt(lines[1]) || 0 : 0;
    memo.push(`  💰 Yesterday's Sales: **${yesterdayTotal.toLocaleString()} Ks**`);
    memo.push(``);
  } catch {}

  // System health
  try {
    const health = await sshExec(`for s in psvibe-api psvibe-dashboard psvibe-sale-bot psvibe_customer_bot; do echo "$(systemctl is-active $s.service)" ; done`, 5000);
    const allHealthy = !health.includes('inactive') && !health.includes('failed');
    memo.push(`  🖥️ **System:** ${allHealthy ? '✅ All services healthy' : '⚠️ Some services down'}`);
    memo.push(``);
  } catch {
    memo.push(`  🖥️ **System:** ⚠️ Cannot check`);
  }

  // Reminders
  memo.push(`  📌 **Reminders:**`);
  memo.push(`  • BI Report: Auto-sends at 9:30 AM`);
  memo.push(`  • Git Backup: Auto-commits at 11 PM`);
  memo.push(`  • Memory: Consolidates at 10 PM`);
  memo.push(``);
  memo.push(`_Have a great day Boss!_ 🤖🔥`);

  state.todaySent = true;
  saveState(state);

  return [memo.join('\n')];
}

// ── 4. Full check ──
async function fullCheck() {
  const allAlerts = [
    ...await checkSalesMilestones(),
    ...await checkServices(),
    ...await dailyMemo(),
  ];
  return allAlerts;
}

// ── Reset daily lock ──
function resetDaily() {
  const state = loadState();
  state.todaySent = false;
  state.milestones = { last5M: false, last10M: false };
  saveState(state);
  console.log('✅ Daily notification state reset');
}

// ── CLI ──
async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0] || 'check';

  switch (cmd) {
    case 'check':
    case 'status':
      const alerts = await fullCheck();
      if (alerts.length === 0) {
        console.log('✅ No notifications pending');
        return;
      }
      alerts.forEach(a => {
        console.log(a);
        console.log('');
      });
      break;

    case 'sales':
      const salesAlerts = await checkSalesMilestones();
      salesAlerts.forEach(a => console.log(a));
      if (salesAlerts.length === 0) console.log('✅ No sales milestones triggered');
      break;

    case 'services':
      const svcAlerts = await checkServices();
      svcAlerts.forEach(a => console.log(a));
      if (svcAlerts.length === 0) console.log('✅ All services healthy');
      break;

    case 'daily-memo':
      const memoAlerts = await dailyMemo();
      memoAlerts.forEach(a => console.log(a));
      if (memoAlerts.length === 0) console.log('⏰ Already sent today or outside memo window');
      break;

    case 'reset':
      resetDaily();
      break;

    default:
      console.log(`
🔔 Notification Center Usage:
  check       → Full check (all alert types)
  sales       → Sales milestone check
  services    → Service health check
  daily-memo  → Send morning digest
  reset       → Reset daily flags
`);
  }
}

main().catch(err => {
  console.error(`❌ Error: ${err.message}`);
  process.exit(1);
});
