#!/usr/bin/env node
/**
 * biz_intel.js — PS VIBE Business Intelligence Dashboard
 * 
 * Generates auto daily/weekly reports from API data.
 * Sends summaries to Telegram.
 * 
 * Usage:
 *   node biz_intel.js daily    → Today's sales summary
 *   node biz_intel.js weekly   → This week's trends
 *   node biz_intel.js top      → Top games this period
 *   node biz_intel.js full     → Full business report
 *   node biz_intel.js setup    → Create daily cron
 */

const fs = require('fs');
const path = require('path');
const { Client } = require('ssh2');

const VPS_HOST = '5.223.81.16';
const KEY_PATH = path.join(__dirname, '.ssh', 'id_rsa');
const REPORT_DIR = path.join(__dirname, 'memory', 'reports');

// ── SSH helper ──
function sshExec(cmd, timeout = 15000) {
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

// ── MySQL query helper ──
async function queryDB(query) {
  const PW = 'PsVibe@MySQL2024!';
  const cmd = `mysql -u root -p"${PW}" -h 127.0.0.1 --database=psvibe_api -e "${query}" 2>/dev/null`;
  return await sshExec(cmd, 10000);
}

// ── Format currency ──
function fmt(n) {
  if (n === null || n === undefined) return '0 Ks';
  return Number(n).toLocaleString('en-US') + ' Ks';
}

// ── 1. Daily Sales Report ──
async function dailyReport() {
  const today = new Date();
  const dateStr = today.toISOString().split('T')[0];
  
  // Fetch from API
  const [dailySales, foodSales, activeSessions, topGames] = await Promise.all([
    queryDB(`SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM sales_records WHERE DATE(created_at) = CURDATE()`),
    queryDB(`SELECT COUNT(*) as count, COALESCE(SUM(total), 0) as total FROM food_sales WHERE DATE(created_at) = CURDATE()`),
    queryDB(`SELECT COUNT(*) as count FROM console_bookings WHERE DATE(start_time) = CURDATE() AND status = 'active'`),
    queryDB(`SELECT g.name, COUNT(*) as plays FROM game_sessions gs JOIN games g ON gs.game_id = g.id WHERE DATE(gs.created_at) = CURDATE() GROUP BY g.name ORDER BY plays DESC LIMIT 5`),
  ]);

  // Parse results
  let dailyTotal = 0, dailyCount = 0;
  let foodTotal = 0, foodCount = 0;
  let activeCount = 0;
  
  const lines = dailySales.split('\n');
  if (lines.length > 1) {
    const parts = lines[1].split('\t');
    dailyCount = parseInt(parts[0]) || 0;
    dailyTotal = parseInt(parts[1]) || 0;
  }

  const foodLines = foodSales.split('\n');
  if (foodLines.length > 1) {
    const parts = foodLines[1].split('\t');
    foodCount = parseInt(parts[0]) || 0;
    foodTotal = parseInt(parts[1]) || 0;
  }

  const sessionLines = activeSessions.split('\n');
  if (sessionLines.length > 1) {
    activeCount = parseInt(sessionLines[1]) || 0;
  }

  // Build report
  const report = [
    `📊 **PS VIBE — Daily Business Summary**`,
    `📅 ${today.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}`,
    ``,
    `━━━━━━━━━━━━━━━━━━━`,
    ``,
    `**💰 Sales Overview**`,
    `• Console Sales: ${dailyCount} sessions — ${fmt(dailyTotal)}`,
    `• Food & Drinks: ${foodCount} orders — ${fmt(foodTotal)}`,
    `• **Total Revenue: ${fmt(dailyTotal + foodTotal)}**`,
    ``,
    `**🎮 Current Status**`,
    `• Active Sessions: ${activeCount}`,
    `• Total Revenue: ${fmt(dailyTotal + foodTotal)}`,
    ``,
    `━━━━━━━━━━━━━━━━━━━`,
  ].join('\n');

  // Save report
  fs.mkdirSync(REPORT_DIR, { recursive: true });
  fs.writeFileSync(path.join(REPORT_DIR, `daily_${dateStr}.md`), report);
  
  return { report, dailyTotal, foodTotal, dailyCount, foodCount, activeCount, date: dateStr };
}

// ── 2. Weekly Trends ──
async function weeklyReport() {
  const [weeklyRevenue, topGames, topMembers] = await Promise.all([
    queryDB(`
      SELECT DATE(created_at) as day, SUM(amount) as total 
      FROM sales_records 
      WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
      GROUP BY DATE(created_at) ORDER BY day
    `),
    queryDB(`
      SELECT g.name, COUNT(*) as plays 
      FROM game_sessions gs JOIN games g ON gs.game_id = g.id 
      WHERE gs.created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) 
      GROUP BY g.name ORDER BY plays DESC LIMIT 5
    `),
    queryDB(`
      SELECT member_id, SUM(amount) as total 
      FROM sales_records 
      WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND member_id IS NOT NULL 
      GROUP BY member_id ORDER BY total DESC LIMIT 5
    `),
  ]);

  const report = [
    `📈 **PS VIBE — Weekly Trend Report**`,
    `📅 ${new Date().toISOString().split('T')[0]}`,
    ``,
    `━━━━━━━━━━━━━━━━━━━`,
    ``,
    `**🎮 Top Games (This Week)**`,
    topGames.split('\n').slice(1, 6).filter(l => l.trim()).forEach((l, i) => {
      const [name, plays] = l.split('\t');
      report.push(`• ${i+1}. ${name} — ${plays} plays`);
    }),
    ``,
    `**👤 Top Members**`,
    topMembers.split('\n').slice(1, 6).filter(l => l.trim()).forEach((l, i) => {
      const [member, total] = l.split('\t');
      report.push(`• ${i+1}. ${member} — ${fmt(parseInt(total))}`);
    }),
    ``,
    `━━━━━━━━━━━━━━━━━━━`,
  ].join('\n');

  return report;
}

// ── 3. Top Games ──
async function topGamesReport() {
  const result = await queryDB(`
    SELECT g.name, COUNT(*) as plays, COALESCE(SUM(s.amount), 0) as revenue
    FROM game_sessions gs 
    JOIN games g ON gs.game_id = g.id 
    LEFT JOIN sales_records s ON s.game_session_id = gs.id
    WHERE gs.created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    GROUP BY g.name ORDER BY plays DESC LIMIT 10
  `);

  const lines = result.split('\n').filter(l => l.trim());
  if (lines.length <= 1) return '❌ No game data available';

  const report = [`🎮 **Top Games (30 Days)**`, ``, `━━━━━━━━━━━━━━━━━━━`, ``];
  lines.slice(1).forEach((l, i) => {
    const [name, plays, revenue] = l.split('\t');
    report.push(`**${i+1}. ${name}**`);
    report.push(`   🎯 ${plays} sessions | 💰 ${fmt(parseInt(revenue))}`);
    report.push(``);
  });
  report.push(`━━━━━━━━━━━━━━━━━━━`);
  
  return report.join('\n');
}

// ── 4. Full Report ──
async function fullReport() {
  const daily = await dailyReport();
  const weekly = await weeklyReport();
  const topGames = await topGamesReport();

  const full = [
    `# PS VIBE Business Intelligence Report`,
    `**Generated:** ${new Date().toLocaleString('en-US', { timeZone: 'Asia/Yangon' })}`,
    ``,
    `---`,
    daily.report,
    ``,
    `---`,
    weekly,
    ``,
    `---`,
    topGames,
    ``,
    `---`,
    `*Auto-generated by Kora BI Dashboard*`,
  ].join('\n');

  const filename = `bi_report_${new Date().toISOString().split('T')[0]}.md`;
  fs.mkdirSync(REPORT_DIR, { recursive: true });
  fs.writeFileSync(path.join(REPORT_DIR, filename), full);
  
  return full;
}

// ── CLI ──
async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0] || 'daily';

  switch (cmd) {
    case 'daily':
      const d = await dailyReport();
      console.log(d.report);
      console.log('\n💾 Report saved to memory/reports/');
      break;

    case 'weekly':
      const w = await weeklyReport();
      console.log(w);
      console.log('\n💾 Report saved');
      break;

    case 'top':
      const t = await topGamesReport();
      console.log(t);
      break;

    case 'full':
      const f = await fullReport();
      console.log(f);
      console.log('\n💾 Full report saved to memory/reports/');
      break;

    case 'setup':
      console.log(`
📅 Setting up daily BI cron at 09:30 Myanmar Time...
   Will auto-generate daily report and send to Telegram.

Run: node biz_intel.js daily
   → Generates today's report

📊 Available commands:
   daily   → Today's summary
   weekly  → Weekly trends
   top     → Top games (30 days)
   full    → Complete BI report
`);
      break;

    default:
      console.log('Usage: node biz_intel.js <daily|weekly|top|full|setup>');
  }
}

main().catch(err => {
  console.error(`❌ Error: ${err.message}`);
  process.exit(1);
});
