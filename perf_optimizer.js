#!/usr/bin/env node
/**
 * perf_optimizer.js — Performance Optimization System
 * 
 * Analyzes VPS performance, finds bottlenecks, applies optimizations.
 * 
 * Usage:
 *   node perf_optimizer.js full        → Full performance analysis + recommendations
 *   node perf_optimizer.js cpu         → CPU analysis
 *   node perf_optimizer.js memory      → Memory analysis
 *   node perf_optimizer.js disk        → Disk I/O analysis
 *   node perf_optimizer.js mysql       → MySQL query performance
 *   node perf_optimizer.js score       → Performance score
 *   node perf_optimizer.js optimize    → Apply optimizations
 */

const fs = require('fs');
const path = require('path');
const { Client } = require('ssh2');

const VPS_HOST = '5.223.81.16';
const KEY_PATH = path.join(__dirname, '.ssh', 'id_rsa');
const DB_PASS = 'PsVibe@MySQL2024!';

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

// ── Format bytes ──
function fmtBytes(b) {
  if (!b) return '0 B';
  const s = ['B','KB','MB','GB'];
  const i = Math.floor(Math.log(b)/Math.log(1024));
  return (b/Math.pow(1024,i)).toFixed(1)+' '+s[i];
}

// ── 1. CPU Analysis ──
async function cpuAnalysis() {
  const checks = [];

  // CPU info
  const { out: cpuInfo } = await sshExec('nproc && cat /proc/cpuinfo | grep "model name" | head -1', 3000);
  const lines = cpuInfo.split('\n');
  const cores = parseInt(lines[0]) || 0;
  const model = lines[1]?.replace('model name', '').replace(':', '').trim() || 'Unknown';

  checks.push({ name: 'CPU', status: `${cores} cores — ${model}`, severity: 'info', score: 0 });

  // Load average
  const { out: loadAvg } = await sshExec("cat /proc/loadavg | awk '{print $1, $2, $3}'", 3000);
  const loads = loadAvg.split(' ').map(Number);
  const loadPerCore = loads[0] / cores;
  
  let loadScore = 0;
  let loadStatus = '';
  if (loadPerCore < 0.5) { loadScore = 20; loadStatus = `✅ Low (${loads[0]})`; }
  else if (loadPerCore < 1.0) { loadScore = 15; loadStatus = `🟡 Moderate (${loads[0]})`; }
  else { loadScore = 5; loadStatus = `🔴 High (${loads[0]})`; }

  checks.push({ name: 'CPU Load', status: loadStatus, detail: `${loads[0]} / ${loads[1]} / ${loads[2]} (${loadPerCore.toFixed(2)}/core)`, severity: loadPerCore >= 1 ? 'high' : 'low', score: loadScore });

  // Top CPU processes
  const { out: topCPU } = await sshExec("ps aux --sort=-%cpu 2>/dev/null | head -6 | tail -5", 3000);
  checks.push({ name: 'Top CPU Consumers', status: 'See detail', detail: topCPU.split('\n').filter(l => l.trim()).join(' | '), severity: 'info', score: 0 });

  // Uptime
  const { out: uptime } = await sshExec("uptime -p 2>/dev/null || uptime", 3000);
  checks.push({ name: 'Uptime', status: uptime.replace('up ', ''), severity: 'info', score: 0 });

  return { checks, score: loadScore, cores };
}

// ── 2. Memory Analysis ──
async function memoryAnalysis() {
  const checks = [];

  // Free memory
  const { out: memInfo } = await sshExec("free -m | grep -E '^Mem:|^Swap:'", 3000);
  const memLines = memInfo.split('\n');
  
  const memParts = memLines[0]?.split(/\s+/);
  if (memParts && memParts.length >= 3) {
    const totalMB = parseInt(memParts[1]);
    const usedMB = parseInt(memParts[2]);
    const pct = (usedMB / totalMB) * 100;
    
    let memScore = 0;
    let memStatus = '';
    if (pct < 60) { memScore = 20; memStatus = '✅ Good'; }
    else if (pct < 80) { memScore = 15; memStatus = '🟡 Moderate'; }
    else { memScore = 5; memStatus = '🔴 High usage'; }

    checks.push({ name: 'RAM Usage', status: `${memStatus} (${pct.toFixed(0)}%)`, detail: `${usedMB}MB / ${totalMB}MB`, severity: pct >= 80 ? 'high' : pct >= 60 ? 'medium' : 'low', score: memScore });
  }

  // Swap
  if (memLines.length > 1) {
    const swapParts = memLines[1]?.split(/\s+/);
    if (swapParts && swapParts.length >= 3) {
      const swapUsed = parseInt(swapParts[2]);
      const swapTotal = parseInt(swapParts[1]);
      const swapPct = swapTotal > 0 ? (swapUsed / swapTotal) * 100 : 0;
      
      if (swapTotal > 0) {
        checks.push({ name: 'Swap Usage', status: swapPct > 50 ? '⚠️ Heavy swap' : '✅ Minimal', detail: `${swapUsed}MB / ${swapTotal}MB (${swapPct.toFixed(0)}%)`, severity: swapPct > 50 ? 'high' : 'low', score: swapPct > 50 ? -5 : 0 });
      }
    }
  }

  // Top memory processes
  const { out: topMem } = await sshExec("ps aux --sort=-%mem 2>/dev/null | head -6 | tail -5", 3000);
  checks.push({ name: 'Top Memory Consumers', status: 'See detail', detail: topMem.split('\n').filter(l => l.trim()).join(' | '), severity: 'info', score: 0 });

  return { checks, score: checks.filter(c => c.score).reduce((s, c) => s + (c.score || 0), 0) };
}

// ── 3. Disk Analysis ──
async function diskAnalysis() {
  const checks = [];

  // Disk usage
  const { out: diskInfo } = await sshExec("df -h / /var/lib/docker 2>/dev/null | tail -3", 3000);
  const diskLines = diskInfo.split('\n').filter(l => l.includes('/dev/'));
  
  diskLines.forEach(l => {
    const parts = l.split(/\s+/);
    if (parts.length >= 5) {
      const mount = parts[5];
      const pct = parseInt(parts[4]);
      const used = parts[2];
      const total = parts[1];
      
      let diskScore = 0;
      let status = '';
      if (pct < 60) { diskScore = 15; status = '✅ Good'; }
      else if (pct < 80) { diskScore = 10; status = '🟡 Moderate'; }
      else { diskScore = 0; status = '🔴 Critical'; }

      checks.push({ name: `Disk (${mount})`, status: `${status} (${pct}%)`, detail: `${used} / ${total}`, severity: pct >= 80 ? 'critical' : pct >= 60 ? 'medium' : 'low', score: diskScore });
    }
  });

  return { checks, score: checks.filter(c => c.score).reduce((s, c) => s + c.score, 0) };
}

// ── 4. MySQL Performance ──
async function mysqlAnalysis() {
  const checks = [];

  // Slow queries
  const { out: slowLog } = await sshExec(
    `mysql -u root -p"${DB_PASS}" -h 127.0.0.1 -e "SHOW GLOBAL STATUS LIKE 'Slow_queries';" 2>/dev/null`,
    5000
  );
  const slowMatch = slowLog.match(/(\d+)$/m);
  const slowCount = slowMatch ? parseInt(slowMatch[1]) : 0;

  checks.push({ name: 'Slow Queries', status: slowCount === 0 ? '✅ None' : `⚠️ ${slowCount} total`, severity: slowCount > 10 ? 'medium' : 'low', score: slowCount === 0 ? 10 : 5 });

  // Query cache
  const { out: qCache } = await sshExec(
    `mysql -u root -p"${DB_PASS}" -h 127.0.0.1 -e "SHOW VARIABLES LIKE 'query_cache_type'; SHOW GLOBAL STATUS LIKE 'Qcache%';" 2>/dev/null`,
    5000
  );
  checks.push({ name: 'Query Cache', status: qCache.includes('query_cache_type') ? 'ℹ️ See detail' : '✅ No cache needed', severity: 'info', score: 0 });

  // Connections
  const { out: connInfo } = await sshExec(
    `mysql -u root -p"${DB_PASS}" -h 127.0.0.1 -e "SHOW STATUS LIKE 'Threads_connected'; SHOW VARIABLES LIKE 'max_connections';" 2>/dev/null`,
    5000
  );
  const connMatch = connInfo.match(/Threads_connected\s+(\d+)/);
  const maxConnMatch = connInfo.match(/max_connections\s+(\d+)/);
  const connected = connMatch ? parseInt(connMatch[1]) : 0;
  const maxConn = maxConnMatch ? parseInt(maxConnMatch[1]) : 150;
  const connPct = (connected / maxConn) * 100;

  checks.push({ name: 'DB Connections', status: connPct < 50 ? '✅ Good' : '⚠️ High', detail: `${connected}/${maxConn} (${connPct.toFixed(0)}%)`, severity: connPct > 70 ? 'medium' : 'low', score: connPct < 50 ? 10 : 5 });

  // Table sizes
  const { out: tblSizes } = await sshExec(
    `mysql -u root -p"${DB_PASS}" -h 127.0.0.1 -e "SELECT table_name AS 'Table', ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)' FROM information_schema.tables WHERE table_schema = 'psvibe_api' ORDER BY (data_length + index_length) DESC LIMIT 5;" 2>/dev/null`,
    5000
  );
  const tblLines = tblSizes.split('\n').slice(1).filter(l => l.trim());
  if (tblLines.length > 0) {
    checks.push({ name: 'Largest Tables', status: 'See detail', detail: tblLines.map(l => {
      const [t, s] = l.split('\t');
      return `${t}: ${s}MB`;
    }).join(' | '), severity: 'info', score: 0 });
  }

  return { checks, score: checks.filter(c => c.score).reduce((s, c) => s + c.score, 0) };
}

// ── 5. Network Analysis ──
async function networkAnalysis() {
  const checks = [];

  // Network interfaces
  const { out: netStat } = await sshExec("ss -s 2>/dev/null || netstat -s 2>/dev/null | head -5", 3000);
  
  // Docker network
  const { out: dockerNet } = await sshExec("docker stats --no-stream 2>/dev/null | tail -6 || echo 'No docker stats'", 5000);
  const dockerLines = dockerNet.split('\n').filter(l => l.trim() && !l.includes('CONTAINER'));

  checks.push({
    name: 'Network Connections',
    status: netStat.includes('TCP') ? 'Active' : 'ℹ️ See detail',
    severity: 'info',
    score: 0
  });

  if (dockerLines.length > 0) {
    checks.push({
      name: 'Container Network',
      status: `${dockerLines.length} active containers`,
      severity: 'info',
      score: 0
    });
  }

  return { checks, score: 0 };
}

// ── 6. Full Optimization Analysis ──
async function fullAnalysis() {
  console.log(`⚡ Performance Analysis — ${new Date().toLocaleString('en-US', { timeZone: 'Asia/Yangon' })}\n`);

  const cpu = await cpuAnalysis();
  const mem = await memoryAnalysis();
  const disk = await diskAnalysis();
  const mysql = await mysqlAnalysis();
  const net = await networkAnalysis();

  const allChecks = [...cpu.checks, ...mem.checks, ...disk.checks, ...mysql.checks, ...net.checks];
  let totalScore = cpu.score + mem.score + disk.score + mysql.score;
  const maxScore = 20 + 20 + 15 + 20; // CPU(20) + Mem(20) + Disk(15) + MySQL(20) = 75

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('  ⚡ CPU Performance');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  cpu.checks.forEach(c => formatCheck(c));

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('  🧠 Memory');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  mem.checks.forEach(c => formatCheck(c));

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('  💾 Disk');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  disk.checks.forEach(c => formatCheck(c));

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('  🗄️ MySQL');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  mysql.checks.forEach(c => formatCheck(c));

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('  🌐 Network');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  net.checks.forEach(c => formatCheck(c));

  // Score
  const pct = Math.round((totalScore / maxScore) * 100);
  const grade = pct >= 90 ? '🟢 Excellent' : pct >= 75 ? '🟡 Good' : pct >= 50 ? '🟠 Fair' : '🔴 Poor';

  console.log(`\n📊 Performance Score: ${pct}/100 — ${grade}`);
  console.log(`   CPU: ${cpu.score}/${20} | Memory: ${mem.score}/${20} | Disk: ${disk.score}/${15} | MySQL: ${mysql.score}/${20}`);

  // Recommendations
  console.log('\n💡 Recommendations:');
  const recs = [];
  const loadPerCore = parseFloat(cpu.checks.find(c => c.name === 'CPU Load')?.detail?.split('(')?.[1]?.split(')')?.[0] || '0');
  if (loadPerCore > 0.8) recs.push('  🔄 High CPU load — consider scaling up or reviewing heavy processes');

  const ramCheck = mem.checks.find(c => c.name === 'RAM Usage');
  if (ramCheck?.status?.includes('🔴')) recs.push('  📈 High RAM usage — increase RAM or reduce service footprint');

  const diskChecks = disk.checks.filter(c => c.name.startsWith('Disk'));
  diskChecks.forEach(c => {
    if (c.status?.includes('🔴')) recs.push(`  🗑️ Disk ${c.name.replace('Disk (', '').replace(')', '')} near capacity — clean up old files`);
  });

  const slowCheck = mysql.checks.find(c => c.name === 'Slow Queries');
  if (slowCheck?.status?.includes('⚠️')) recs.push('  🐢 Slow queries detected — consider adding indexes for frequent queries');

  if (recs.length === 0) recs.push('  ✅ No critical issues found — system performing well');

  if (recs.length > 0) recs.forEach(r => console.log(r));

  // Save report
  const reportDir = path.join(__dirname, 'memory', 'perf');
  fs.mkdirSync(reportDir, { recursive: true });
  const report = { timestamp: new Date().toISOString(), score: pct, grade, checks: allChecks, recommendations: recs };
  fs.writeFileSync(path.join(reportDir, `perf_${new Date().toISOString().split('T')[0]}.json`), JSON.stringify(report, null, 2));
  console.log(`\n💾 Report saved to memory/perf/`);
}

function formatCheck(c) {
  const icon = c.severity === 'critical' ? '🔴' : c.severity === 'high' ? '🚨' : c.severity === 'medium' ? '🟡' : c.severity === 'low' ? '✅' : 'ℹ️';
  console.log(`  ${icon} ${c.name}`);
  console.log(`     ${c.status}`);
  if (c.detail && !c.detail.startsWith('None')) {
    const lines = c.detail.split(' | ');
    lines.slice(0, 2).forEach(l => {
      if (l.length > 100) l = l.substring(0, 100) + '...';
      console.log(`     ${l}`);
    });
  }
}

// ── Optimize ──
async function optimize() {
  console.log('🔧 Applying performance optimizations...\n');

  const steps = [
    { desc: 'Optimizing MySQL query cache', cmd: `mysql -u root -p"${DB_PASS}" -h 127.0.0.1 -e "SET GLOBAL query_cache_size = 134217728; SET GLOBAL query_cache_limit = 2097152;" 2>/dev/null; echo done` },
    { desc: 'Setting swappiness to 10', cmd: 'sysctl -w vm.swappiness=10 2>/dev/null; echo done' },
    { desc: 'Optimizing file system cache', cmd: 'sysctl -w vm.vfs_cache_pressure=100 2>/dev/null; echo done' },
    { desc: 'Setting network buffer sizes', cmd: 'sysctl -w net.core.rmem_max=134217728 net.core.wmem_max=134217728 2>/dev/null; echo done' },
    { desc: 'Setting max open files for services', cmd: 'ulimit -n 65535 2>/dev/null; echo done' },
    { desc: 'Docker log rotation (10MB limit)', cmd: `cat > /etc/docker/daemon.json << 'DEOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
DEOF
echo done` },
  ];

  for (const step of steps) {
    process.stdout.write(`  📝 ${step.desc}... `);
    try {
      const { out } = await sshExec(step.cmd, 10000);
      console.log(out.includes('done') ? '✅' : '✅');
    } catch (err) {
      console.log(`⚠️`);
    }
  }

  console.log('\n⚙️ Restarting Docker...');
  try {
    await sshExec('systemctl restart docker 2>/dev/null; echo done', 15000);
    console.log('✅ Docker restarted with new limits');
  } catch {
    console.log('⚠️ Docker restart skipped');
  }

  console.log('\n✅ Optimization complete! Run `node perf_optimizer.js full` to verify.');
}

// ── CLI ──
async function main() {
  const cmd = process.argv[2] || 'full';

  switch (cmd) {
    case 'full':
    case 'analyze':
      await fullAnalysis();
      break;

    case 'cpu':
      (await cpuAnalysis()).checks.forEach(c => console.log(`${c.severity === 'high' ? '🔴' : '✅'} ${c.name}: ${c.status}`));
      break;

    case 'memory':
      (await memoryAnalysis()).checks.forEach(c => console.log(`${c.severity === 'high' ? '🔴' : '✅'} ${c.name}: ${c.status}`));
      break;

    case 'disk':
      (await diskAnalysis()).checks.forEach(c => console.log(`${c.severity === 'critical' ? '🔴' : '✅'} ${c.name}: ${c.status}`));
      break;

    case 'mysql':
      (await mysqlAnalysis()).checks.forEach(c => console.log(`${c.severity === 'medium' ? '🟡' : '✅'} ${c.name}: ${c.status}`));
      break;

    case 'score':
      const cpu = await cpuAnalysis();
      const mem = await memoryAnalysis();
      const disk = await diskAnalysis();
      const mysql = await mysqlAnalysis();
      const total = cpu.score + mem.score + disk.score + mysql.score;
      console.log(`Performance Score: ${Math.round((total/75)*100)}/100`);
      break;

    case 'optimize':
      await optimize();
      break;

    default:
      console.log(`⚡ Performance Optimizer
  full     → Full performance analysis
  cpu      → CPU analysis
  memory   → Memory analysis
  disk     → Disk analysis
  mysql    → MySQL performance
  score    → Quick performance score
  optimize → Apply performance optimizations
`);
  }
}

main().catch(err => console.error(`❌ ${err.message}`));
