#!/usr/bin/env node
/**
 * uptime_monitor.js — Comprehensive Uptime Monitoring System
 * 
 * Monitors all PS VIBE services + Docker containers + API health.
 * Maintains uptime history and alerts on failures.
 * 
 * Usage:
 *   node uptime_monitor.js check       → Full health check
 *   node uptime_monitor.js history     → Show uptime history
 *   node uptime_monitor.js alert       → Send alert if services down
 *   node uptime_monitor.js dashboard   → Pretty health dashboard
 */

const fs = require('fs');
const path = require('path');
const { Client } = require('ssh2');

const VPS_HOST = '5.223.81.16';
const VPS_USER = 'root';
const KEY_PATH = path.join(__dirname, '.ssh', 'id_rsa');
const LOG_PATH = path.join(__dirname, 'memory', 'uptime_log.json');
const HISTORY_SIZE = 1000;

// ── Service definitions ──
const SERVICES = {
  systemd: [
    { name: 'psvibe-api', cmd: 'systemctl is-active psvibe-api.service' },
    { name: 'psvibe-dashboard', cmd: 'systemctl is-active psvibe-dashboard.service' },
    { name: 'psvibe-sale-bot', cmd: 'systemctl is-active psvibe-sale-bot.service' },
    { name: 'psvibe_customer_bot', cmd: 'systemctl is-active psvibe_customer_bot.service' },
    { name: 'psvibe-watchdog', cmd: 'systemctl is-active psvibe-watchdog.service' },
  ],
  docker: [
    { name: 'psvibe-mysql', cmd: "docker inspect --format='{{.State.Status}}' psvibe-mysql" },
    { name: 'construction-bot', cmd: "docker inspect --format='{{.State.Status}}' construction_bot" },
    { name: 'n8n', cmd: "docker inspect --format '{{.State.Status}}' aungchanmyint-n8n-1 2>/dev/null; docker inspect --format '{{.State.Health.Status}}' aungchanmyint-n8n-1 2>/dev/null || echo running" },
    { name: 'caddy', cmd: "docker inspect --format='{{.State.Status}}' aungchanmyint-caddy-1" },
    { name: 'nova', cmd: "docker inspect --format='{{.State.Health.Status}}' oc-nova || echo running" },
    { name: 'coco', cmd: "docker inspect --format='{{.State.Health.Status}}' oc-coco || echo running" },
  ],
  api: [
    { name: 'API Health', cmd: 'curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ 2>/dev/null || echo "FAIL"' },
    { name: 'Dashboard', cmd: 'curl -s -o /dev/null -w "%{http_code}" http://localhost:9090 2>/dev/null || echo "FAIL"' },
  ],
  process: [
    { name: 'ACM Wallet Bot', cmd: 'pgrep -f "ACM-Personal-Wallet" > /dev/null 2>&1 && echo active || echo inactive' },
    { name: 'Coordination Dashboard', cmd: 'pgrep -f "dashboard.py.*9090" > /dev/null 2>&1 && echo active || echo inactive' },
    { name: 'Service Watchdog', cmd: 'pgrep -f "service_watchdog" > /dev/null 2>&1 && echo active || echo inactive' },
  ],
};

// ── SSH helper ──
function sshExec(cmd, timeout = 10000) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let out = '';
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { conn.end(); reject(err); return; }
        stream.on('data', d => out += d.toString().trim());
        stream.stderr.on('data', d => out += ' STDERR:' + d.toString().trim());
        stream.on('close', () => { conn.end(); resolve(out.trim()); });
      });
    });
    conn.on('error', reject);
    conn.connect({
      host: VPS_HOST, port: 22, username: VPS_USER,
      privateKey: fs.readFileSync(KEY_PATH),
      readyTimeout: 10000,
    });
    setTimeout(() => { conn.end(); reject(new Error('SSH timeout')); }, timeout);
  });
}

// ── Logging ──
function loadLog() {
  try {
    if (fs.existsSync(LOG_PATH)) {
      return JSON.parse(fs.readFileSync(LOG_PATH, 'utf8'));
    }
  } catch {}
  return { history: [], summary: { total: 0, failures: 0, uptime: 0 } };
}

function saveLog(log) {
  fs.mkdirSync(path.dirname(LOG_PATH), { recursive: true });
  // Trim old history
  if (log.history.length > HISTORY_SIZE) {
    log.history = log.history.slice(-HISTORY_SIZE);
  }
  fs.writeFileSync(LOG_PATH, JSON.stringify(log, null, 2));
}

// ── Full check ──
async function fullCheck() {
  const startTime = Date.now();
  const results = [];
  let totalServices = 0;
  let failedServices = 0;

  for (const [group, services] of Object.entries(SERVICES)) {
    for (const svc of services) {
      totalServices++;
      let status = 'unknown';
      let output = '';
      try {
        output = await sshExec(svc.cmd, 8000);
        status = output.startsWith('active') || output.startsWith('running') || output.startsWith('healthy') || output.startsWith('Up') || output === '200' ? '✅' : '❌';
        if (status === '❌') failedServices++;
      } catch (err) {
        status = '❌';
        output = err.message.substring(0, 50);
        failedServices++;
      }
      results.push({
        group,
        name: svc.name,
        status,
        output: output.substring(0, 60),
        timestamp: new Date().toISOString(),
      });
    }
  }

  // System metrics
  let cpu, mem, disk, dockerRunning;
  try {
    cpu = await sshExec("top -bn1 | head -5 | grep '%Cpu' | awk '{print $2}'", 5000);
    mem = await sshExec("free -m | awk 'NR==2{printf \"%.0f%%\", $3*100/$2}'", 5000);
    disk = await sshExec("df -h / | tail -1 | awk '{print $5}'", 5000);
    dockerRunning = await sshExec("docker ps --format '{{.Names}}' | wc -l", 5000);
  } catch {}

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  const uptimePct = totalServices > 0 ? Math.round(((totalServices - failedServices) / totalServices) * 100) : 0;

  const check = {
    timestamp: new Date().toISOString(),
    duration: `${elapsed}s`,
    total: totalServices,
    passed: totalServices - failedServices,
    failed: failedServices,
    uptimePct,
    services: results,
    metrics: { cpu, mem, disk, dockerRunning },
  };

  // Save to history
  const log = loadLog();
  log.history.push({
    timestamp: check.timestamp,
    total: check.total,
    failed: check.failed,
    uptimePct,
    duration: check.duration,
  });
  log.summary = {
    total: log.history.length,
    failures: log.history.filter(h => h.failed > 0).length,
    avgUptime: Math.round(log.history.reduce((s, h) => s + h.uptimePct, 0) / Math.max(log.history.length, 1)),
    lastCheck: check.timestamp,
  };
  saveLog(log);

  return check;
}

// ── Display ──
function displayCheck(check) {
  console.log(`🔍 Uptime Monitor — ${check.timestamp}`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`⏱️  Duration: ${check.duration}`);
  console.log(`📊 Uptime: ${check.uptimePct}% (${check.passed}/${check.total})`);
  if (check.metrics.cpu) console.log(`💻 CPU: ${check.metrics.cpu}% | MEM: ${check.metrics.mem} | DISK: ${check.metrics.disk} | 🐳 Docker: ${check.metrics.dockerRunning}`);

  let lastGroup = '';
  for (const svc of check.services) {
    if (svc.group !== lastGroup) {
      const labels = { systemd: '📋 Systemd', docker: '🐳 Docker', api: '🌐 API', process: '⚙️ Process' };
      console.log(`\n${labels[svc.group] || svc.group}:`);
      lastGroup = svc.group;
    }
    console.log(`  ${svc.status} ${svc.name}${svc.status === '❌' ? ` → ${svc.output}` : ''}`);
  }

  const log = loadLog();
  console.log(`\n📈 Historical: ${log.summary.total} checks | Avg Uptime: ${log.summary.avgUptime}% | Failures: ${log.summary.failures}`);
}

function displayHistory(limit = 20) {
  const log = loadLog();
  const entries = log.history.slice(-limit);
  console.log(`📊 Uptime History (last ${entries.length}/${log.history.length} checks)`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`Avg Uptime: ${log.summary.avgUptime}% | Total: ${log.summary.total} checks | ${log.summary.failures} with failures`);
  console.log();
  for (const h of entries) {
    const date = new Date(h.timestamp);
    const time = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    const status = h.failed > 0 ? '⚠️' : '✅';
    console.log(`  ${status} ${h.uptimePct}% (${h.passed || (h.total - h.failed)}/${h.total}) — ${time} [${h.duration}]`);
  }
}

// ── Alert if failures ──
async function checkAlert() {
  const check = await fullCheck();
  if (check.failed > 0) {
    const failedList = check.services.filter(s => s.status === '❌').map(s => `  ❌ ${s.name}: ${s.output}`).join('\n');
    return {
      alert: true,
      message: `🚨 Uptime Alert — ${check.failed} service(s) down!\n\n${failedList}\n\n📊 Uptime: ${check.uptimePct}%\n⏱️ ${check.timestamp}`,
      check,
    };
  }
  return { alert: false, check };
}

// ── CLI ──
async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0] || 'check';

  switch (cmd) {
    case 'check':
      const check = await fullCheck();
      displayCheck(check);
      break;

    case 'history':
      displayHistory(parseInt(args[1]) || 20);
      break;

    case 'alert':
      const alert = await checkAlert();
      if (alert.alert) {
        console.log(alert.message);
      } else {
        console.log(`✅ All ${alert.check.total} services healthy (${alert.check.uptimePct}%)`);
      }
      break;

    case 'dashboard':
      console.log(`
╔══════════════════════════════════╗
║    PS VIBE UPTIME DASHBOARD     ║
╚══════════════════════════════════╝
`);
      const dCheck = await fullCheck();
      displayCheck(dCheck);
      break;

    default:
      console.log('Usage: node uptime_monitor.js <check|history|alert|dashboard>');
  }
}

main().catch(err => {
  console.error(`❌ Error: ${err.message}`);
  process.exit(1);
});
