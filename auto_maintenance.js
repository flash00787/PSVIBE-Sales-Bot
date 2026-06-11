#!/usr/bin/env node
/**
 * 🧹 Auto Maintenance Mode — Kora Workspace
 *
 * Nightly cleanup (00:00 Myanmar Time / 17:30 UTC):
 *   - Log rotation (truncate old logs)
 *   - MySQL optimize tables
 *   - Docker prune unused images/volumes
 *   - Check disk space
 *
 * Morning health check (08:00 Myanmar Time / 01:30 UTC):
 *   - All service status
 *   - Yesterday's sales summary
 *   - Member activity report
 *   - System health report → memory/maintenance/
 *
 * Run: node auto_maintenance.js [nightly|morning|--help]
 */

const { mysqlQuery, checkSystemResources, sshExec } = require('./lib/ssh_vps');
const fs = require('fs');
const path = require('path');

const LOG_DIR = path.join(__dirname, 'memory', 'maintenance');
if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });

const TIMESTAMP = () => new Date().toISOString().replace(/[:.]/g, '-');
const DATESTAMP = () => {
  const d = new Date();
  d.setTime(d.getTime() + 6.5 * 3600000); // Myanmar time offset
  return d.toISOString().split('T')[0];
};

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
}

// ═══════════════════════════════════════════
// NIGHTLY CLEANUP (00:00 MMT)
// ═══════════════════════════════════════════
async function nightlyCleanup() {
  log('🌙 Starting NIGHTLY CLEANUP...');
  const report = { date: DATESTAMP(), type: 'nightly', actions: [], errors: [] };

  // 1. MySQL optimize tables
  try {
    log('  📊 Optimizing MySQL tables...');
    const tables = (await mysqlQuery('SHOW TABLES'))
      .split('\n')
      .filter(l => l.trim() && !l.includes('Tables_in'))
      .map(l => l.trim());

    let optimized = 0;
    for (const table of tables) {
      if (!table) continue;
      await mysqlQuery(`OPTIMIZE TABLE \`${table}\``);
      optimized++;
    }
    report.actions.push(`Optimized ${optimized} MySQL tables`);
    log(`  ✅ Optimized ${optimized} MySQL tables`);
  } catch (e) {
    report.errors.push(`MySQL optimize failed: ${e.message}`);
    log(`  ❌ MySQL optimize failed: ${e.message}`);
  }

  // 2. Analyze tables for query planner
  try {
    const tables = (await mysqlQuery('SHOW TABLES'))
      .split('\n')
      .filter(l => l.trim() && !l.includes('Tables_in'))
      .map(l => l.trim());

    for (const table of tables) {
      if (!table) continue;
      await mysqlQuery(`ANALYZE TABLE \`${table}\``);
    }
    report.actions.push('MySQL ANALYZE completed');
    log('  ✅ MySQL ANALYZE completed');
  } catch (e) {
    report.errors.push(`MySQL ANALYZE failed: ${e.message}`);
  }

  // 3. Docker system prune (clean up old images, containers)
  try {
    log('  🐳 Pruning Docker system...');
    const pruneResult = await sshExec('docker system prune -f --volumes --filter "until=48h" 2>&1', 30000);
    report.actions.push(`Docker prune: ${pruneResult.trim().split('\n').pop() || 'done'}`);
    log(`  ✅ Docker cleanup done`);
  } catch (e) {
    report.errors.push(`Docker prune failed: ${e.message}`);
    log(`  ❌ Docker prune failed: ${e.message}`);
  }

  // 4. Log rotation — truncate old logs
  try {
    log('  📝 Rotating logs...');
    const logFiles = ['/root/psvibe_api_server/api.log'];
    let rotated = 0;
    for (const lf of logFiles) {
      try {
        const size = await sshExec(`wc -c < ${lf} 2>/dev/null || echo 0`, 5000);
        const bytes = parseInt(size.trim()) || 0;
        if (bytes > 10 * 1024 * 1024) { // > 10MB
          await sshExec(`cp ${lf} ${lf}.$(date +%Y%m%d).bak && > ${lf}`, 5000);
          rotated++;
          log(`    Rotated ${lf} (was ${(bytes/1024/1024).toFixed(1)}MB)`);
        }
      } catch { /* ignore missing files */ }
    }
    report.actions.push(`Rotated ${rotated} log files`);
    log(`  ✅ Rotated ${rotated} log files`);
  } catch (e) {
    report.errors.push(`Log rotation: ${e.message}`);
  }

  // 5. Check disk space
  try {
    const df = await checkSystemResources();
    log(`  💾 Disk check done`);
    report.diskStatus = df.disk;
  } catch (e) {
    report.errors.push(`Disk check: ${e.message}`);
  }

  // Save report
  const reportFile = path.join(LOG_DIR, `nightly_${TIMESTAMP()}.json`);
  fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
  log(`📄 Report saved: ${reportFile}`);
  log('🌙 NIGHTLY CLEANUP COMPLETE');
  return report;
}

// ═══════════════════════════════════════════
// MORNING HEALTH CHECK (08:00 MMT)
// ═══════════════════════════════════════════
async function morningHealthCheck() {
  log('☀️  Starting MORNING HEALTH CHECK...');
  const report = { date: DATESTAMP(), type: 'morning', timestamp: new Date().toISOString() };

  // 1. Yesterday's sales
  try {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const ymd = yesterday.toISOString().split('T')[0];

    const sales = (await mysqlQuery(
      `SELECT COUNT(*) as txns, COALESCE(SUM(net), 0) as total, COALESCE(SUM(gross), 0) as gross, COALESCE(SUM(discount), 0) as discounts FROM sales_daily WHERE sale_date = '${ymd}'`
    )).trim().split('\n');

    if (sales.length >= 2) {
      const headers = sales[0].split('\t');
      const values = sales[1].split('\t');
      report.yesterdaySales = {};
      headers.forEach((h, i) => { report.yesterdaySales[h] = values[i]; });
      log(`  📊 Yesterday (${ymd}): ${report.yesterdaySales.total || 0} MMK, ${report.yesterdaySales.txns || 0} transactions`);
    }
  } catch (e) {
    report.yesterdaySales = { error: e.message };
    log(`  ❌ Sales query failed: ${e.message}`);
  }

  // 2. Topups yesterday
  try {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const ymd = yesterday.toISOString().split('T')[0];

    const topups = (await mysqlQuery(
      `SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total, SUM(mins_added) as mins FROM topup_log WHERE DATE(topup_date) = '${ymd}'`
    )).trim().split('\n');

    if (topups.length >= 2) {
      const vals = topups[1].split('\t');
      report.yesterdayTopups = { count: vals[0], total: vals[1], mins: vals[2] };
      log(`  💰 Yesterday topups: ${report.yesterdayTopups.count || 0}, ${report.yesterdayTopups.total || 0} MMK, ${report.yesterdayTopups.mins || 0} mins`);
    }
  } catch (e) {
    report.yesterdayTopups = { error: e.message };
  }

  // 3. Active members count
  try {
    const members = await mysqlQuery('SELECT COUNT(*) as cnt FROM member_wallets WHERE balance_mins > 0');
    report.activeMembers = members.trim().split('\n')[1]?.split('\t')[0] || '?';
    log(`  👥 Active members: ${report.activeMembers}`);
  } catch (e) {
    report.activeMembers = 'error';
  }

  // 4. Console status
  try {
    const consoles = await mysqlQuery('SELECT console_id, status, console_type FROM console_status');
    report.consoleStatus = consoles.trim();
    const freeCount = (consoles.match(/Free/g) || []).length;
    const occupiedCount = (consoles.match(/Occupied|Active/g) || []).length;
    log(`  🎮 Consoles: ${freeCount} free, ${occupiedCount} occupied`);
  } catch (e) {
    report.consoleStatus = 'error';
  }

  // 5. System health
  try {
    const resources = await checkSystemResources();
    report.systemHealth = { docker: resources.docker, cpu: resources.cpu?.split('\n')[2]?.trim() };

    // Parse memory
    const memMatch = resources.mem?.match(/Mem:\s+\d+\s+(\d+)\s+(\d+)/);
    if (memMatch) {
      const total = parseInt(memMatch[1]);
      const used = parseInt(memMatch[2]);
      report.systemHealth.memoryPercent = ((used / total) * 100).toFixed(1);
    }

    // Parse disk
    const diskMatch = resources.disk?.match(/(\d+)%\s+\//);
    if (diskMatch) report.systemHealth.diskPercent = diskMatch[1];

    log(`  🖥️  System: Memory ${report.systemHealth.memoryPercent || '?'}%, Disk ${report.systemHealth.diskPercent || '?'}%`);
  } catch (e) {
    report.systemHealth = { error: e.message };
  }

  // 6. Docker container status
  try {
    const docker = await sshExec('docker ps --format "{{.Names}}: {{.Status}}"', 10000);
    report.dockerContainers = docker.trim();
    const unhealthy = (docker.match(/unhealthy|Exited|restarting/g) || []).length;
    log(`  🐳 Docker: ${unhealthy > 0 ? `⚠️ ${unhealthy} unhealthy!` : 'All healthy ✅'}`);
  } catch (e) {
    report.dockerContainers = 'error';
  }

  // 7. Recent bookings
  try {
    const today = new Date().toISOString().split('T')[0];
    const bookings = await mysqlQuery(
      `SELECT COUNT(*) as count FROM console_booking WHERE booking_date = '${today}'`
    );
    report.todayBookings = bookings.trim().split('\n')[1]?.split('\t')[0] || '0';
    log(`  📅 Today's bookings: ${report.todayBookings}`);
  } catch (e) {
    report.todayBookings = 'error';
  }

  // Overall status
  report.overallStatus = 'healthy';
  const issues = [];
  if (report.systemHealth?.diskPercent && parseInt(report.systemHealth.diskPercent) > 90) issues.push('disk > 90%');
  if (report.systemHealth?.memoryPercent && parseFloat(report.systemHealth.memoryPercent) > 95) issues.push('memory > 95%');
  if (report.dockerContainers?.includes('unhealthy')) issues.push('unhealthy containers');

  if (issues.length > 0) {
    report.overallStatus = '⚠️ ' + issues.join(', ');
  }

  // Save report
  const reportFile = path.join(LOG_DIR, `morning_${TIMESTAMP()}.json`);
  fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
  log(`📄 Report saved: ${reportFile}`);

  // Print summary
  console.log('\n═══════════════════════════════════════════');
  console.log('  ☀️  MORNING HEALTH REPORT');
  console.log('═══════════════════════════════════════════');
  console.log(`  📊 Yesterday Sales:  ${report.yesterdaySales?.total || '?'} MMK (${report.yesterdaySales?.txns || '?'} txns)`);
  console.log(`  💰 Yesterday Topups: ${report.yesterdayTopups?.total || '?'} MMK`);
  console.log(`  👥 Active Members:   ${report.activeMembers}`);
  console.log(`  📅 Today Bookings:   ${report.todayBookings}`);
  console.log(`  🐳 Docker:           ${report.dockerContainers?.includes('unhealthy') ? '⚠️ Issues' : '✅ Healthy'}`);
  console.log(`  💾 Disk:             ${report.systemHealth?.diskPercent || '?'}%`);
  console.log(`  🧠 Memory:           ${report.systemHealth?.memoryPercent || '?'}%`);
  console.log(`  🏥 Overall:          ${report.overallStatus}`);
  console.log('═══════════════════════════════════════════\n');

  log('☀️  MORNING HEALTH CHECK COMPLETE');
  return report;
}

// ═══════════════════════════════════════════
// TEST MODE — Quick health check (no changes)
// ═══════════════════════════════════════════
async function testHealthCheck() {
  log('🔍 TEST MODE — Quick Health Check (read-only)');
  console.log('');

  const results = [];

  // 1. Check disk space
  try {
    const df = await checkSystemResources();
    const diskLine = (df.disk || '').split('\n').filter(l => l.includes('/'));
    results.push({ check: '💾 Disk Space', status: '✅', detail: diskLine[0] || df.disk?.substring(0, 80) || 'checked' });
  } catch (e) {
    results.push({ check: '💾 Disk Space', status: '⚠️', detail: `Error: ${e.message}` });
  }

  // 2. Check Docker containers
  try {
    const docker = await sshExec('docker ps --format "{{.Names}}: {{.Status}}"', 10000);
    const unhealthy = (docker.match(/unhealthy|Exited|restarting/g) || []).length;
    const total = docker.trim().split('\n').filter(l => l).length;
    results.push({ check: '🐳 Docker', status: unhealthy === 0 ? '✅' : '⚠️', detail: `${total} containers, ${unhealthy} unhealthy` });
  } catch (e) {
    results.push({ check: '🐳 Docker', status: '⚠️', detail: `Error: ${e.message}` });
  }

  // 3. Check system services
  try {
    const services = ['psvibe-sale-bot', 'psvibe-api', 'psvibe_customer_bot', 'cloudflared-tunnel'];
    for (const svc of services) {
      try {
        const out = await sshExec(`systemctl is-active ${svc} 2>/dev/null`, 5000);
        const active = out.trim() === 'active';
        results.push({ check: `  📡 ${svc}`, status: active ? '✅' : '❌', detail: out.trim() });
      } catch {
        results.push({ check: `  📡 ${svc}`, status: '❌', detail: 'check failed' });
      }
    }
  } catch (e) {
    results.push({ check: '📡 Services', status: '⚠️', detail: `Error: ${e.message}` });
  }

  // 4. Check recent sales (quick DB query)
  try {
    const today = new Date().toISOString().split('T')[0];
    const sales = await mysqlQuery(`SELECT COUNT(*) as txns, COALESCE(SUM(net), 0) as total FROM sales_daily WHERE sale_date = '${today}'`);
    const parts = sales.trim().split('\n').filter(l => l);
    if (parts.length >= 2) {
      const vals = parts[1].split('\t');
      results.push({ check: '📊 Today Sales', status: '✅', detail: `${vals[1] || 0} MMK, ${vals[0] || 0} txns` });
    }
  } catch (e) {
    results.push({ check: '📊 Today Sales', status: '⚠️', detail: `Error: ${e.message}` });
  }

  // 5. Check console status
  try {
    const consoles = await mysqlQuery('SELECT console_id, status, console_type FROM console_status');
    const freeCount = (consoles.match(/Free/g) || []).length;
    const occupiedCount = (consoles.match(/Occupied|Active/g) || []).length;
    results.push({ check: '🎮 Consoles', status: occupiedCount > 0 ? '✅' : '⚠️', detail: `${freeCount} free, ${occupiedCount} occupied` });
  } catch (e) {
    results.push({ check: '🎮 Consoles', status: '⚠️', detail: `Error: ${e.message}` });
  }

  // Print summary
  console.log(`${'═'.repeat(50)}`);
  console.log('  🔍 HEALTH CHECK SUMMARY (read-only)');
  console.log(`${'═'.repeat(50)}`);
  let passed = 0, warned = 0, failed = 0;
  for (const r of results) {
    console.log(`  ${r.status} ${r.check}: ${r.detail}`);
    if (r.status === '✅') passed++;
    else if (r.status === '⚠️') warned++;
    else failed++;
  }
  console.log(`${'═'.repeat(50)}`);
  console.log(`  ✅ ${passed} passed  ⚠️ ${warned} warnings  ❌ ${failed} failed`);
  console.log(`  ℹ️  No changes were made — this is read-only`);
  console.log(`${'═'.repeat(50)}`);

  const report = {
    date: DATESTAMP(),
    type: 'test',
    timestamp: new Date().toISOString(),
    results: results.map(r => ({ check: r.check, status: r.status, detail: r.detail })),
    summary: { passed, warned, failed },
  };
  const reportFile = path.join(LOG_DIR, `test_${TIMESTAMP()}.json`);
  fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
  log(`📄 Report saved: ${reportFile}`);

  return report;
}

// ═══════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════
async function main() {
  const args = process.argv.slice(2);
  const mode = args[0] || 'auto';

  if (args.includes('--help') || args.includes('-h')) {
    console.log(`🧹 Auto Maintenance Mode — Kora Workspace
Usage:
  node auto_maintenance.js nightly  — Run nightly cleanup
  node auto_maintenance.js morning  — Run morning health check
  node auto_maintenance.js test     — Quick health check (no changes made)
  node auto_maintenance.js          — Auto-detect (based on Myanmar time)`);
    process.exit(0);
  }

  if (mode === 'test') return testHealthCheck();

  // Auto-detect mode based on Myanmar time
  if (mode === 'auto') {
    const now = new Date();
    const mmHour = (now.getUTCHours() + 6.5) % 24;
    if (mmHour >= 0 && mmHour < 1) {
      return nightlyCleanup();
    } else if (mmHour >= 8 && mmHour < 9) {
      return morningHealthCheck();
    } else {
      log('⚠️  Not in scheduled window. Use nightly|morning to force.');
      process.exit(0);
    }
  }

  if (mode === 'nightly') return nightlyCleanup();
  if (mode === 'morning') return morningHealthCheck();

  log('❌ Unknown mode. Use: nightly, morning, or --help');
  process.exit(1);
}

main().catch(e => {
  console.error('❌ Fatal error:', e.message);
  process.exit(1);
});
