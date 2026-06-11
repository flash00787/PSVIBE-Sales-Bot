#!/usr/bin/env node
/**
 * 🔔 Smart Alert System — Kora Workspace
 * 
 * Detects anomalies across PS VIBE operations:
 * 1. Sudden member balance drops (fraud/waste detection)
 * 2. Console offline detection
 * 3. Sales vs target gap
 * 4. System resource spikes (CPU > 80%, disk > 85%, memory > 90%)
 * 5. Service health (Docker containers, systemd units)
 *
 * Run: node smart_alerts.js [--once] [--verbose]
 * Cron: every 30 minutes
 */

const { mysqlQuery, checkSystemResources, sshExec } = require('./lib/ssh_vps');
const fs = require('fs');
const path = require('path');

const LOG_DIR = path.join(__dirname, 'memory', 'alerts');
const STATE_FILE = path.join(LOG_DIR, 'alert_state.json');
const HISTORY_FILE = path.join(LOG_DIR, 'alert_history.json');

// Thresholds
const THRESHOLDS = {
  balanceDropPercent: 30,        // 30% drop in 24h = alert
  balanceDropAbsolute: 5000,    // Or 5000 min absolute drop
  cpuPercent: 80,
  diskPercent: 85,
  memoryPercent: 90,
  salesVsTargetGap: 40,         // 40% below target
  dailySalesTarget: 50000,      // MMK daily target
};

// Ensure log dir
if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });

function loadState() {
  try { return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); }
  catch { return { lastRun: null, lastBalances: {}, lastSales: {} }; }
}

function saveState(state) {
  state.lastRun = new Date().toISOString();
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

function logAlert(alert) {
  const alerts = (() => { try { return JSON.parse(fs.readFileSync(HISTORY_FILE,'utf8')); } catch { return []; } })();
  alerts.unshift({ ...alert, timestamp: new Date().toISOString() });
  if (alerts.length > 500) alerts.length = 500;
  fs.writeFileSync(HISTORY_FILE, JSON.stringify(alerts, null, 2));
}

function fmt(s) { return typeof s === 'string' ? s.trim() : String(s); }

/**
 * Parse MySQL tabular output into array of objects
 */
function parseTable(output) {
  const lines = output.trim().split('\n');
  if (lines.length < 2) return [];
  // Skip warning line if present
  let headerIdx = 0;
  while (headerIdx < lines.length && !lines[headerIdx].includes('\t')) headerIdx++;
  if (headerIdx >= lines.length) return [];

  const headers = lines[headerIdx].split('\t');
  const rows = [];
  for (let i = headerIdx + 1; i < lines.length; i++) {
    const vals = lines[i].split('\t');
    if (vals.length !== headers.length) continue;
    const row = {};
    headers.forEach((h, j) => { row[h] = vals[j]; });
    rows.push(row);
  }
  return rows;
}

// ═══════════════════════════════════════════
// 1. MEMBER BALANCE DROP DETECTION
// ═══════════════════════════════════════════
async function checkBalanceAnomalies(state, verbose) {
  const alerts = [];
  
  // Check member_wallets for today's balance vs yesterday
  const wallets = parseTable(await mysqlQuery(
    'SELECT member_id, member_name, balance_mins, total_spend, last_updated FROM member_wallets WHERE balance_mins > 0 ORDER BY balance_mins DESC'
  ));

  if (wallets.length === 0) {
    if (verbose) console.log('  [balance] No wallet data found');
    return alerts;
  }

  // Check for very low balances (below 30 min threshold)
  const lowBalanceMembers = wallets.filter(w => parseInt(w.balance_mins) < 30);
  if (lowBalanceMembers.length > 0) {
    const names = lowBalanceMembers.map(w => `${w.member_name || w.member_id} (${w.balance_mins}m)`).join(', ');
    alerts.push({
      type: 'low_balance',
      severity: 'warning',
      message: `⚠️ ${lowBalanceMembers.length} members have low balance (<30 min): ${names}`,
      count: lowBalanceMembers.length,
    });
  }

  // Compare with last run state for sudden drops
  const prevBalances = state.lastBalances || {};
  for (const w of wallets) {
    const prev = prevBalances[w.member_id];
    const current = parseInt(w.balance_mins) || 0;
    if (prev && prev > 0) {
      const dropPercent = ((prev - current) / prev) * 100;
      const dropAbsolute = prev - current;
      if (dropAbsolute > 0 && (dropPercent >= THRESHOLDS.balanceDropPercent || dropAbsolute >= THRESHOLDS.balanceDropAbsolute)) {
        alerts.push({
          type: 'balance_drop',
          severity: 'critical',
          message: `🚨 Balance drop for ${w.member_name || w.member_id}: ${prev}m → ${current}m (${dropPercent.toFixed(1)}% drop, -${dropAbsolute}m)`,
          memberId: w.member_id,
          memberName: w.member_name,
          dropPercent,
          dropAbsolute,
        });
      }
    }
    prevBalances[w.member_id] = current;
  }
  state.lastBalances = prevBalances;

  return alerts;
}

// ═══════════════════════════════════════════
// 2. CONSOLE OFFLINE DETECTION
// ═══════════════════════════════════════════
async function checkConsoleStatus(verbose) {
  const alerts = [];
  const consoles = parseTable(await mysqlQuery(
    'SELECT console_id, status, console_type, current_member, start_time, last_updated FROM console_status'
  ));

  for (const c of consoles) {
    if (c.status !== 'Free' && c.status !== 'Occupied' && c.status !== 'Booked' && c.status !== 'Active') {
      alerts.push({
        type: 'console_status',
        severity: 'warning',
        message: `⚠️ Console ${c.console_id} has unusual status: "${c.status}"`,
        consoleId: c.console_id,
      });
    }
    // Check if console has been occupied too long (> 8 hours)
    if ((c.status === 'Occupied' || c.status === 'Active') && c.start_time && c.start_time !== 'NULL') {
      const startTime = new Date(c.start_time);
      const hoursRunning = (Date.now() - startTime.getTime()) / 3600000;
      if (hoursRunning > 8) {
        alerts.push({
          type: 'long_session',
          severity: 'warning',
          message: `⏰ Console ${c.console_id} occupied for ${hoursRunning.toFixed(1)}h by ${c.current_member || '?'} — may need checkout`,
          consoleId: c.console_id,
          hoursRunning: hoursRunning.toFixed(1),
        });
      }
    }
    // Check if last_updated is stale (> 2 hours)
    if (c.last_updated && c.last_updated !== 'NULL') {
      const lastUpdate = new Date(c.last_updated);
      const hoursStale = (Date.now() - lastUpdate.getTime()) / 3600000;
      if (hoursStale > 2) {
        alerts.push({
          type: 'stale_console',
          severity: 'info',
          message: `📡 Console ${c.console_id} last updated ${hoursStale.toFixed(1)}h ago`,
          consoleId: c.console_id,
        });
      }
    }
  }

  if (verbose) console.log(`  [console] Checked ${consoles.length} consoles`);
  return alerts;
}

// ═══════════════════════════════════════════
// 3. SALES VS TARGET GAP
// ═══════════════════════════════════════════
async function checkSalesGap(verbose) {
  const alerts = [];
  const today = new Date().toISOString().split('T')[0];

  const sales = parseTable(await mysqlQuery(
    `SELECT COALESCE(SUM(net), 0) as total_sales, COUNT(*) as txns FROM sales_daily WHERE sale_date = '${today}'`
  ));

  const todaySales = parseFloat(sales[0]?.total_sales || 0);
  const txns = parseInt(sales[0]?.txns || 0);

  if (verbose) console.log(`  [sales] Today: ${todaySales} MMK (${txns} transactions)`);

  if (todaySales > 0 && todaySales < THRESHOLDS.dailySalesTarget * (1 - THRESHOLDS.salesVsTargetGap / 100)) {
    alerts.push({
      type: 'sales_gap',
      severity: 'warning',
      message: `📉 Today's sales (${todaySales} MMK) are below 60% of target (${THRESHOLDS.dailySalesTarget} MMK)`,
      currentSales: todaySales,
      target: THRESHOLDS.dailySalesTarget,
      gapPercent: ((1 - todaySales / THRESHOLDS.dailySalesTarget) * 100).toFixed(1),
    });
  }

  return alerts;
}

// ═══════════════════════════════════════════
// 4. SYSTEM RESOURCE SPIKES
// ═══════════════════════════════════════════
async function checkSystemSpikes(verbose) {
  const alerts = [];
  const resources = await checkSystemResources();

  // Parse CPU
  if (resources.cpu && typeof resources.cpu === 'string' && !resources.cpu.startsWith('ERROR')) {
    const cpuLines = resources.cpu.split('\n');
    for (const line of cpuLines) {
      const match = line.match(/(\d+\.?\d*)\s*id/);
      if (match) {
        const idle = parseFloat(match[1]);
        const used = 100 - idle;
        if (used > THRESHOLDS.cpuPercent) {
          alerts.push({
            type: 'cpu_spike',
            severity: 'critical',
            message: `🔥 CPU usage at ${used.toFixed(1)}% (threshold: ${THRESHOLDS.cpuPercent}%)`,
            cpuPercent: used.toFixed(1),
          });
        }
        break;
      }
    }
  }

  // Parse Memory
  if (resources.mem && typeof resources.mem === 'string' && !resources.mem.startsWith('ERROR')) {
    const memLines = resources.mem.split('\n');
    for (const line of memLines) {
      if (line.startsWith('Mem:')) {
        const parts = line.trim().split(/\s+/);
        const total = parseFloat(parts[1]);
        const used = parseFloat(parts[2]);
        if (total > 0) {
          const usedPercent = (used / total) * 100;
          if (usedPercent > THRESHOLDS.memoryPercent) {
            alerts.push({
              type: 'memory_spike',
              severity: 'critical',
              message: `🧠 Memory usage at ${usedPercent.toFixed(1)}% (threshold: ${THRESHOLDS.memoryPercent}%)`,
              memoryPercent: usedPercent.toFixed(1),
            });
          }
        }
        break;
      }
    }
  }

  // Parse Disk
  if (resources.disk && typeof resources.disk === 'string' && !resources.disk.startsWith('ERROR')) {
    const diskLines = resources.disk.split('\n');
    for (const line of diskLines) {
      if (line.includes('/') && line.includes('%')) {
        const match = line.match(/(\d+)%/);
        if (match) {
          const used = parseInt(match[1]);
          if (used > THRESHOLDS.diskPercent) {
            alerts.push({
              type: 'disk_spike',
              severity: 'critical',
              message: `💾 Disk usage at ${used}% (threshold: ${THRESHOLDS.diskPercent}%)`,
              diskPercent: used,
            });
          }
          break;
        }
      }
    }
  }

  // Parse Docker status
  if (resources.docker && typeof resources.docker === 'string' && !resources.docker.startsWith('ERROR')) {
    const dockerLines = resources.docker.split('\n');
    for (const line of dockerLines) {
      if (line.includes('Exited') || line.includes('unhealthy') || line.includes('restarting')) {
        const name = line.split(' ')[0];
        alerts.push({
          type: 'service_down',
          severity: 'critical',
          message: `🔴 Docker container ${name} is not healthy: ${line}`,
          container: name,
        });
      }
      if (line.includes('health: starting')) {
        const name = line.split(' ')[0];
        alerts.push({
          type: 'service_starting',
          severity: 'warning',
          message: `🟡 Docker container ${name} is still starting`,
          container: name,
        });
      }
    }
  }

  if (verbose) console.log(`  [system] Checked CPU/MEM/DISK/Docker`);
  return alerts;
}

// ═══════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════
async function main() {
  const args = process.argv.slice(2);
  const once = args.includes('--once');
  const verbose = args.includes('--verbose');

  const state = loadState();
  const allAlerts = [];

  if (verbose) console.log('🔔 Smart Alert System — Running checks...\n');

  try {
    const balanceAlerts = await checkBalanceAnomalies(state, verbose);
    allAlerts.push(...balanceAlerts);
  } catch (e) {
    console.error('  ❌ Balance check failed:', e.message);
    allAlerts.push({ type: 'error', severity: 'error', message: `Balance check failed: ${e.message}` });
  }

  try {
    const consoleAlerts = await checkConsoleStatus(verbose);
    allAlerts.push(...consoleAlerts);
  } catch (e) {
    console.error('  ❌ Console check failed:', e.message);
    allAlerts.push({ type: 'error', severity: 'error', message: `Console check failed: ${e.message}` });
  }

  try {
    const salesAlerts = await checkSalesGap(verbose);
    allAlerts.push(...salesAlerts);
  } catch (e) {
    console.error('  ❌ Sales check failed:', e.message);
    allAlerts.push({ type: 'error', severity: 'error', message: `Sales check failed: ${e.message}` });
  }

  try {
    const systemAlerts = await checkSystemSpikes(verbose);
    allAlerts.push(...systemAlerts);
  } catch (e) {
    console.error('  ❌ System check failed:', e.message);
    allAlerts.push({ type: 'error', severity: 'error', message: `System check failed: ${e.message}` });
  }

  saveState(state);

  // Log all alerts
  for (const alert of allAlerts) {
    logAlert(alert);
  }

  // Summary
  const criticals = allAlerts.filter(a => a.severity === 'critical');
  const warnings = allAlerts.filter(a => a.severity === 'warning');
  const infos = allAlerts.filter(a => a.severity === 'info');
  const errors = allAlerts.filter(a => a.severity === 'error');

  console.log(`\n📊 Alert Summary: ${allAlerts.length} total`);
  console.log(`  🔴 Critical: ${criticals.length}`);
  console.log(`  🟡 Warning:  ${warnings.length}`);
  console.log(`  🔵 Info:     ${infos.length}`);
  console.log(`  ❌ Errors:   ${errors.length}`);

  if (criticals.length > 0) {
    console.log('\n🚨 CRITICAL ALERTS:');
    criticals.forEach(a => console.log(`  ${a.message}`));
  }
  if (warnings.length > 0) {
    console.log('\n⚠️  WARNINGS:');
    warnings.forEach(a => console.log(`  ${a.message}`));
  }

  return { total: allAlerts.length, criticals: criticals.length, warnings: warnings.length, alerts: allAlerts };
}

// Run
main()
  .then(result => {
    console.log(`\n✅ Smart Alert check complete at ${new Date().toISOString()}`);
    if (!result) process.exit(0);
  })
  .catch(e => {
    console.error('❌ Smart Alert system fatal error:', e.message);
    process.exit(1);
  });
