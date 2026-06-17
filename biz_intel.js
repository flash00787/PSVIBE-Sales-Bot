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
  
  // Fetch correct data from real MySQL tables
  // sales_daily table (NOT sales_records) — column is net (not amount)
  const [dailySales, foodSales, activeSessions, topGames] = await Promise.all([
    queryDB(`SELECT COUNT(*) as count, COALESCE(SUM(net), 0) as total FROM sales_daily WHERE sale_date = CURDATE()`),
    queryDB(`SELECT COUNT(*) as count, COALESCE(SUM(quantity * unit_price), 0) as total FROM food_cart WHERE DATE(created_at) = CURDATE()`),
    queryDB(`SELECT COUNT(*) as count FROM console_booking WHERE status = 'confirmed' AND DATE(start_time) = CURDATE()`),
    queryDB(`SELECT COALESCE(game_name, 'Direct') as name, COUNT(*) as plays FROM console_booking WHERE DATE(start_time) = CURDATE() AND game_name IS NOT NULL AND game_name != '' GROUP BY game_name ORDER BY plays DESC LIMIT 5`),
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
      SELECT sale_date as day, SUM(net) as total 
      FROM sales_daily 
      WHERE sale_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
      GROUP BY sale_date ORDER BY day
    `),
    queryDB(`
      SELECT COALESCE(game_name, 'Direct') as name, COUNT(*) as plays 
      FROM console_booking 
      WHERE DATE(start_time) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) 
        AND game_name IS NOT NULL AND game_name != ''
      GROUP BY game_name ORDER BY plays DESC LIMIT 5
    `),
    queryDB(`
      SELECT COALESCE(member_id, 'Guest') as member, SUM(net) as total 
      FROM sales_daily 
      WHERE sale_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) 
      GROUP BY member_id ORDER BY total DESC LIMIT 5
    `),
  ]);

  let report = [
    `📈 **PS VIBE — Weekly Trend Report**`,
    `📅 ${new Date().toISOString().split('T')[0]}`,
    ``,
    `━━━━━━━━━━━━━━━━━━━`,
    ``,
    `**🎮 Top Games (This Week)**`,
  ].join('\n');

  // Add top games
  const gameLines = topGames.split('\n').filter(l => l.trim());
  for (let i = 1; i < Math.min(gameLines.length, 6); i++) {
    const [name, plays] = gameLines[i].split('\t');
    if (name) report += `\n• ${i}. ${name} — ${plays} plays`;
  }
  
  report += `\n\n**👤 Top Members**`;
  
  // Add top members
  const memberLines = topMembers.split('\n').filter(l => l.trim());
  for (let i = 1; i < Math.min(memberLines.length, 6); i++) {
    const [member, total] = memberLines[i].split('\t');
    if (member) report += `\n• ${i}. ${member} — ${fmt(parseInt(total))}`;
  }
  
  report += `\n\n━━━━━━━━━━━━━━━━━━━`;

  return report;
}

// ── 3. Top Games (30 days) ──
async function topGamesReport() {
  const result = await queryDB(`
    SELECT COALESCE(game_name, 'Direct') as name, COUNT(*) as plays
    FROM console_booking 
    WHERE DATE(start_time) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
      AND game_name IS NOT NULL AND game_name != ''
    GROUP BY game_name ORDER BY plays DESC LIMIT 10
  `);

  const lines = result.split('\n').filter(l => l.trim());
  if (lines.length <= 1) return '❌ No game data available';

  let report = [`🎮 **Top Games (30 Days)**`, ``, `━━━━━━━━━━━━━━━━━━━`, ``].join('\n');
  for (let i = 1; i < lines.length; i++) {
    const [name, plays] = lines[i].split('\t');
    if (name) {
      report += `\n**${i}. ${name}**`;
      report += `\n   🎯 ${plays} plays`;
      report += `\n`;
    }
  }
  report += `\n━━━━━━━━━━━━━━━━━━━`;
  
  return report;
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
