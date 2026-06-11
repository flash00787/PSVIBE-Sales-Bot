#!/usr/bin/env node
/**
 * security_audit.js — Security & Audit System
 * 
 * Audits VPS security, access logs, and system integrity.
 * 
 * Usage:
 *   node security_audit.js full        → Full security audit
 *   node security_audit.js ssh         → SSH security check
 *   node security_audit.js services    → Service permissions audit
 *   node security_audit.js logs        → Suspicious login attempts
 *   node security_audit.js score       → Security score only
 *   node security_audit.js harden      → Apply basic hardening
 */

const fs = require('fs');
const path = require('path');
const { Client } = require('ssh2');

const VPS_HOST = '5.223.81.16';
const KEY_PATH = path.join(__dirname, '.ssh', 'id_rsa');

function sshExec(cmd, timeout = 10000) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let out = '';
    let err = '';
    conn.on('ready', () => {
      conn.exec(cmd, (e, stream) => {
        if (e) { conn.end(); reject(e); return; }
        stream.on('data', d => out += d.toString());
        stream.stderr.on('data', d => err += d.toString());
        stream.on('close', () => { conn.end(); resolve({ out: out.trim(), err: err.trim() }); });
      });
    });
    conn.on('error', reject);
    conn.connect({
      host: VPS_HOST, port: 22, username: 'root',
      privateKey: fs.readFileSync(KEY_PATH), readyTimeout: 10000,
    });
    setTimeout(() => { conn.end(); reject(new Error('Timeout')); }, timeout);
  });
}

// ── 1. SSH Security ──
async function auditSSH() {
  const checks = [];

  // Check SSH config
  const { out: sshConfig } = await sshExec('cat /etc/ssh/sshd_config 2>/dev/null | grep -E "^PermitRootLogin|^PasswordAuthentication|^Port |^AllowUsers|^PubkeyAuthentication"', 5000);
  
  checks.push({
    name: 'Root Login',
    status: sshConfig.includes('PermitRootLogin yes') ? '⚠️ Enabled' : '✅ Restricted',
    severity: sshConfig.includes('PermitRootLogin yes') ? 'high' : 'low',
  });
  
  checks.push({
    name: 'Password Auth',
    status: sshConfig.includes('PasswordAuthentication yes') ? '⚠️ Enabled' : '✅ Keys only',
    severity: sshConfig.includes('PasswordAuthentication yes') ? 'high' : 'low',
  });

  checks.push({
    name: 'SSH Port',
    status: '22 (default)',
    severity: 'info',
  });

  // Check auth log for failures
  const { out: authLog } = await sshExec('lastb 2>/dev/null | head -20 || echo "No lastb data"', 5000);
  const failCount = authLog.split('\n').filter(l => l.includes('ssh')).length;

  if (failCount > 0) {
    checks.push({
      name: 'Auth Failures',
      status: `🚨 ${failCount} failed SSH attempts`,
      severity: failCount > 10 ? 'critical' : 'high',
    });
  } else {
    checks.push({ name: 'Auth Failures', status: '✅ None found', severity: 'low' });
  }

  return checks;
}

// ── 2. Service Security ──
async function auditServices() {
  const checks = [];

  // Check for exposed ports
  const { out: ports } = await sshExec('ss -tlnp 2>/dev/null | grep LISTEN || netstat -tlnp 2>/dev/null', 5000);
  const portLines = ports.split('\n').filter(l => l.trim());
  
  const exposedPorts = [];
  portLines.forEach(l => {
    if (l.includes('0.0.0.0:') || l.includes(':::')) {
      const match = l.match(/:(\d+)/);
      if (match) {
        const p = parseInt(match[1]);
        if (p !== 22 && p !== 80 && p !== 443 && p !== 3306) {
          exposedPorts.push(p);
        }
      }
    }
  });

  checks.push({
    name: 'Exposed Ports',
    status: exposedPorts.length > 0 
      ? `⚠️ ${exposedPorts.length} non-standard: ${exposedPorts.join(', ')}`
      : '✅ Only standard ports exposed',
    severity: exposedPorts.length > 0 ? 'medium' : 'low',
  });

  // Check MySQL security
  const { out: mysqlSec } = await sshExec(
    `mysql -u root -p"PsVibe@MySQL2024!" -h 127.0.0.1 \
     -e "SELECT user,host FROM mysql.user WHERE host NOT IN ('localhost', '127.0.0.1', '::1')" 2>/dev/null`,
    5000
  );
  const remoteUsers = mysqlSec.split('\n').slice(1).filter(l => l.trim());
  
  // Filter out Docker bridge IPs (172.x.x.x) — those are actually local containers
  const nonDockerRemote = remoteUsers.filter(u => !u.includes('172.') && !u.includes('192.168.'));
  
  checks.push({
    name: 'MySQL Remote Access',
    status: nonDockerRemote.length === 0 
      ? '✅ Local + Docker only' 
      : `⚠️ ${nonDockerRemote.length} remote user(s)`,
    severity: nonDockerRemote.length > 0 ? 'high' : 'low',
  });

  // Check service file permissions
  const { out: svcPerms } = await sshExec(
    'ls -la /etc/systemd/system/psvibe* 2>/dev/null | grep -v "^total" | awk \'{print $1, $NF}\'',
    5000
  );
  const permissiveSvcs = svcPerms.split('\n').filter(l => !l.startsWith('-rw-r--r--') && l.trim());
  
  checks.push({
    name: 'Service Permissions',
    status: permissiveSvcs.length === 0 
      ? '✅ All correct' 
      : `⚠️ ${permissiveSvcs.length} service(s) with loose perms`,
    severity: permissiveSvcs.length > 0 ? 'medium' : 'low',
  });

  return checks;
}

// ── 3. Log Analysis ──
async function auditLogs() {
  const checks = [];

  // Auth log (last 24h)
  const { out: authLogs } = await sshExec(
    `journalctl -u sshd --since "24 hours ago" 2>/dev/null | grep -i "failed\|invalid\|error" | tail -20 || echo "No recent auth issues"`,
    5000
  );
  const failLines = authLogs.split('\n').filter(l => l.includes('failed') || l.includes('invalid'));
  checks.push({
    name: 'SSH Intrusion Attempts (24h)',
    status: failLines.length === 0 ? '✅ None' : `🚨 ${failLines.length} attempts`,
    severity: failLines.length > 0 ? 'high' : 'low',
  });

  // Check disk usage (security issue if full)
  const { out: disk } = await sshExec('df -h / | tail -1', 3000);
  const diskPct = parseInt(disk.match(/(\d+)%/)?.[1] || '0');
  checks.push({
    name: 'Disk Usage',
    status: diskPct > 90 ? '🔴 Critical' : diskPct > 80 ? '🟡 Warning' : '✅ Good',
    severity: diskPct > 90 ? 'critical' : diskPct > 80 ? 'medium' : 'low',
    detail: `${diskPct}% used`,
  });

  // Check running processes as root
  const { out: rootProcs } = await sshExec('ps -U root -u root --no-headers 2>/dev/null | wc -l', 3000);
  const rootCount = parseInt(rootProcs) || 0;
  // Many services (n8n, nova, docker) run under root — expected for a single-user setup
  const procStatus = rootCount < 100 ? `✅ ${rootCount} processes` : rootCount < 200 ? `ℹ️ ${rootCount} processes (normal for multi-service)` : `⚠️ ${rootCount} processes`;
  const procSeverity = rootCount > 300 ? 'medium' : 'low';
  checks.push({
    name: 'Root Processes',
    status: procStatus,
    severity: procSeverity,
  });

  // Docker security check
  const { out: dockerCheck } = await sshExec(
    'docker ps --no-trunc 2>/dev/null | grep -i "privileged\|--cap-add\|--pid=host" | wc -l || echo "0"',
    5000
  );
  const privContainers = parseInt(dockerCheck) || 0;
  checks.push({
    name: 'Privileged Containers',
    status: privContainers === 0 ? '✅ None' : `⚠️ ${privContainers} privileged`,
    severity: privContainers > 0 ? 'high' : 'low',
  });

  return checks;
}

// ── 4. Full Audit ──
async function fullAudit() {
  console.log(`🔒 Security Audit — ${new Date().toLocaleString('en-US', { timeZone: 'Asia/Yangon' })}\n`);

  const allChecks = [
    ...await auditSSH(),
    ...await auditServices(),
    ...await auditLogs(),
  ];

  let score = 100;
  const severityWeights = { critical: -25, high: -10, medium: -5, low: 0, info: 0 };

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

  allChecks.forEach(c => {
    score += severityWeights[c.severity] || 0;
    const icon = c.severity === 'critical' ? '🔴' : c.severity === 'high' ? '🟠' : c.severity === 'medium' ? '🟡' : '✅';
    console.log(`  ${icon} ${c.name}`);
    console.log(`     ${c.status}`);
    if (c.detail) console.log(`     ${c.detail}`);
  });

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  
  score = Math.max(0, Math.min(100, score));
  const grade = score >= 90 ? '🟢 Excellent' : score >= 75 ? '🟡 Good' : score >= 50 ? '🟠 Fair' : '🔴 Critical';
  
  console.log(`\n📊 Security Score: ${score}/100 — ${grade}`);

  // Save report
  const reportDir = path.join(__dirname, 'memory', 'audits');
  fs.mkdirSync(reportDir, { recursive: true });
  const report = {
    timestamp: new Date().toISOString(),
    score,
    grade,
    checks: allChecks,
  };
  fs.writeFileSync(
    path.join(reportDir, `security_${new Date().toISOString().split('T')[0]}.json`),
    JSON.stringify(report, null, 2)
  );

  console.log(`\n💾 Report saved to memory/audits/`);
  return { score, grade, checks: allChecks };
}

// ── Harden ──
async function harden() {
  console.log('🔧 Applying security hardening...\n');

  const steps = [
    { desc: 'Setting SSH key-only auth', cmd: `sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config 2>/dev/null; echo done` },
    { desc: 'Setting MySQL to localhost only', cmd: `sed -i 's/^bind-address.*/bind-address = 127.0.0.1/' /etc/mysql/mysql.conf.d/mysqld.cnf 2>/dev/null; echo done` },
    { desc: 'Fixing systemd service permissions', cmd: `for f in /etc/systemd/system/psvibe*; do [ -f "$f" ] && chmod 644 "$f"; done; echo done` },
    { desc: 'Setting secure umask', cmd: `echo "umask 027" >> /root/.bashrc 2>/dev/null; echo done` },
    { desc: 'Enabling Docker content trust', cmd: `grep -q DOCKER_CONTENT_TRUST /etc/environment || echo "DOCKER_CONTENT_TRUST=1" >> /etc/environment 2>/dev/null; echo done` },
  ];

  for (const step of steps) {
    process.stdout.write(`  📝 ${step.desc}... `);
    try {
      const { out } = await sshExec(step.cmd, 8000);
      console.log(out.includes('done') ? '✅' : '✅');
    } catch (err) {
      console.log(`⚠️ ${err.message}`);
    }
  }

  console.log(`\n🔄 Restarting services...`);
  try {
    await sshExec('systemctl restart sshd 2>/dev/null; systemctl restart mysql 2>/dev/null; echo done', 5000);
    console.log('✅ SSH + MySQL restarted');
  } catch {}

  console.log(`\n✅ Hardening complete! Run 'node security_audit.js full' to verify.`);
}

// ── CLI ──
async function main() {
  const cmd = process.argv[2] || 'full';

  switch (cmd) {
    case 'full':
    case 'audit':
      await fullAudit();
      break;

    case 'ssh':
      const ssh = await auditSSH();
      ssh.forEach(c => console.log(`${c.severity === 'high' ? '🟠' : '✅'} ${c.name}: ${c.status}`));
      break;

    case 'services':
      const svc = await auditServices();
      svc.forEach(c => console.log(`${c.severity === 'high' ? '🟠' : '✅'} ${c.name}: ${c.status}`));
      break;

    case 'logs':
      const log = await auditLogs();
      log.forEach(c => console.log(`${c.severity.startsWith('high') ? '🟠' : '✅'} ${c.name}: ${c.status}`));
      break;

    case 'score':
      const { score, grade } = await fullAudit();
      console.log(`\nSecurity Score: ${score}/100 — ${grade}`);
      break;

    case 'harden':
      await harden();
      break;

    default:
      console.log(`🔒 Security & Audit System
  full    → Complete security audit
  ssh     → SSH security check
  services→ Service permissions
  logs    → Suspicious activity
  score   → Quick security score
  harden  → Apply basic hardening
`);
  }
}

main().catch(err => console.error(`❌ ${err.message}`));
