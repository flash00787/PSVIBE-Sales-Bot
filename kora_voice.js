#!/usr/bin/env node
/**
 * Kora Voice Assistant — PS VIBE
 * Natural language command processor for staff/admin operations.
 * 
 * HTTP POST /command  → parse query → MySQL → formatted response
 * HTTP POST /tts      → mark text as speakable
 * 
 * Port: 3110
 */

const express = require('express');
const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

// =========================================================================
// Configuration
// =========================================================================

const PORT = process.env.KORA_PORT || 3110;
const HOST = process.env.KORA_HOST || '0.0.0.0';

// MySQL credentials (via env vars with fallback)
const MYSQL_USER = process.env.MYSQL_USER || 'psvibe_user';
const MYSQL_PASSWORD = process.env.MYSQL_PASSWORD || '';
const MYSQL_DB = process.env.MYSQL_DB || 'psvibe_api';

// SSH connection to VPS (if running remotely)
const SSH_HOST = process.env.SSH_HOST || '';
const SSH_PORT = parseInt(process.env.SSH_PORT || '22', 10);
const SSH_USER = process.env.SSH_USER || 'root';
const SSH_KEY_PATH = process.env.SSH_KEY_PATH || '';

// Direct MySQL mode (when running on the VPS itself)
const DIRECT_MYSQL = process.env.DIRECT_MYSQL === 'true' || (!SSH_HOST && !MYSQL_PASSWORD ? false : !!MYSQL_PASSWORD);

// =========================================================================
// MySQL Query Execution
// =========================================================================

/**
 * Execute a MySQL query. Uses SSH if SSH_HOST is configured, otherwise direct.
 */
function queryDB(sql, opts = {}) {
  return new Promise((resolve, reject) => {
    if (SSH_HOST) {
      _queryViaSSH(sql, resolve, reject);
    } else if (DIRECT_MYSQL || MYSQL_PASSWORD) {
      _queryDirect(sql, resolve, reject);
    } else {
      reject(new Error('No MySQL connection configured. Set SSH_HOST or MYSQL_PASSWORD.'));
    }
  });
}

function _queryViaSSH(sql, resolve, reject) {
  const conn = new Client();
  const sshConfig = {
    host: SSH_HOST,
    port: SSH_PORT,
    username: SSH_USER,
    readyTimeout: 10000,
  };
  if (SSH_KEY_PATH && fs.existsSync(SSH_KEY_PATH)) {
    sshConfig.privateKey = fs.readFileSync(SSH_KEY_PATH);
  }

  conn.on('ready', () => {
    const cmd = `docker exec psvibe-mysql mysql -u${MYSQL_USER} -p"${MYSQL_PASSWORD}" ${MYSQL_DB} -e "${sql.replace(/"/g, '\\"')}" 2>&1`;
    conn.exec(cmd, (err, stream) => {
      if (err) { conn.end(); return reject(err); }
      let stdout = '', stderr = '';
      stream.on('data', d => stdout += d.toString());
      stream.stderr.on('data', d => stderr += d.toString());
      stream.on('close', () => {
        conn.end();
        if (stderr && !stderr.includes('Warning')) {
          return reject(new Error(stderr.trim()));
        }
        resolve(_parseTabular(stdout));
      });
    });
  });
  conn.on('error', reject);
  conn.connect(sshConfig);
}

function _queryDirect(sql, resolve, reject) {
  const { exec } = require('child_process');
  const cmd = `docker exec psvibe-mysql mysql -u${MYSQL_USER} -p"${MYSQL_PASSWORD}" ${MYSQL_DB} -e "${sql.replace(/"/g, '\\"')}" 2>&1`;
  exec(cmd, { timeout: 15000 }, (err, stdout, stderr) => {
    if (err) return reject(err);
    if (stderr && !stderr.includes('Warning')) return reject(new Error(stderr.trim()));
    resolve(_parseTabular(stdout));
  });
}

function _parseTabular(output) {
  // Skip MySQL warning lines that start with "mysql:"
  const lines = output.trim().split('\n').filter(l => !l.startsWith('mysql:'));
  if (lines.length < 1) return [];
  
  const headers = lines[0].split('\t');
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split('\t');
    const row = {};
    headers.forEach((h, j) => { row[h] = values[j] !== 'NULL' && values[j] !== undefined ? values[j] : null; });
    rows.push(row);
  }
  return rows;
}

// =========================================================================
// Command Parser — Keyword matching + entity extraction
// =========================================================================

const COMMANDS = [
  // Today Sales
  {
    pattern: /(today|ဒီနေ့|ယနေ့).{0,10}(sales|ဝင်ငွေ|income|ရောင်းရ|ရောင်းအား)/i,
    handler: 'todaySales',
    description: 'Today\'s total sales / ဒီနေ့ဝင်ငွေ',
  },
  // Today Report (full summary)
  {
    pattern: /(today|ဒီနေ့|ယနေ့).{0,5}(report|စာရင်း|အစီရင်ခံ)/i,
    handler: 'todayReport',
    description: 'Today\'s full report / ဒီနေ့စာရင်း',
  },
  {
    pattern: /ps\s*vibe\s*(today|ဒီနေ့|စာရင်း)/i,
    handler: 'todayReport',
    description: null, // alias, no dupe in help
  },
  // This Week Report
  {
    pattern: /(this\s*week|ဒီအပတ်|ယခုအပတ်).{0,10}(report|စာရင်း|အစီရင်ခံ)/i,
    handler: 'weekReport',
    description: 'This week\'s aggregate / ဒီအပတ်စာရင်း',
  },
  // Member Balance
  {
    pattern: /(member|အဖွဲ့ဝင်|member_id).{0,15}(balance|လက်ကျန်|wallet)/i,
    handler: 'memberBalance',
    extract: 'member_id',
    description: 'Check member balance (e.g. "member PSV_A001 balance")',
  },
  // Console Status
  {
    pattern: /(console|စက်ခုံ|ကွန်ဆိုး).{0,10}(status|အခြေနေ|ရှိ|ဘယ်လို)/i,
    handler: 'consoleStatus',
    description: 'Console status board / Console တွေဘယ်လိုရှိလဲ',
  },
  // Today Customers
  {
    pattern: /(today|ဒီနေ့|ယနေ့).{0,15}(customers|လာ|လူ|ယောက်|လူဦးရေ|visitors|members)/i,
    handler: 'todayCustomers',
    description: 'Unique customers today / ဒီနေ့ဘယ်နှစ်ယောက်လာလဲ',
  },
  {
    pattern: /(customers|visitors|လူဦးရေ|လူတွေ).{0,15}(today|ဒီနေ့|ယနေ့)/i,
    handler: 'todayCustomers',
    description: null,
  },
  // Top Games
  {
    pattern: /(top|နာမည်ကြီး|လူကြိုက်များ|popular|most).{0,10}(games|ဂိမ်း|game|played)/i,
    handler: 'topGames',
    description: 'Most played games / နာမည်ကြီးဂိမ်း',
  },
  // Low Inventory
  {
    pattern: /(inventory|စတော့|ကုန်|ပစ္စည်း).{0,10}(low|ခါနီး|နည်း|ပြတ်)/i,
    handler: 'inventoryLow',
    description: 'Low stock items / ကုန်ခါနီးပစ္စည်း',
  },
  // Staff On Duty
  {
    pattern: /(staff|ဝန်ထမ်း|ဘယ်သူ).{0,10}(duty|တာဝန်|ရှိ|လာ|ဝင်)/i,
    handler: 'staffDuty',
    description: 'Staff currently checked in / ဒီနေ့ဘယ်သူတွေရှိလဲ',
  },
  // Today Bookings
  {
    pattern: /(today|ဒီနေ့).{0,10}(booking|ဘွတ်ကင်|ကြိုမှာ)/i,
    handler: 'todayBookings',
    description: 'Today\'s console bookings / ဒီနေ့ဘွတ်ကင်',
  },
  // Help
  {
    pattern: /(help|ကူညီ|ဘာတွေလုပ်|ဘာမေးလို့ရ|command|available)/i,
    handler: 'help',
    description: 'Show available commands / ဘာတွေလုပ်လို့ရလဲ',
  },
];

/**
 * Parse a natural language query and return matched command + extracted entities
 */
function parseCommand(text) {
  if (!text || !text.trim()) {
    return { handler: 'help', entities: {} };
  }

  const clean = text.trim();

  for (const cmd of COMMANDS) {
    const match = clean.match(cmd.pattern);
    if (match) {
      const entities = {};
      if (cmd.extract) {
        // Try to extract entity (e.g., member_id like PSV_A_001, PSV-B001)
        const entityMatch = clean.match(/([A-Z]{2,4}[_-][A-Za-z0-9_-]{3,12})/i);
        if (entityMatch) {
          entities[cmd.extract] = entityMatch[0].toUpperCase().replace(/-/g, '_');
        }
      }
      return { handler: cmd.handler, entities, description: cmd.description };
    }
  }

  // Fallback: try fuzzy matching
  return { handler: 'unknown', entities: {}, description: null };
}

// =========================================================================
// Command Handlers
// =========================================================================

const handlers = {
  async todaySales() {
    const rows = await queryDB(
      `SELECT COUNT(*) as count, COALESCE(SUM(net), 0) as total FROM sales_daily WHERE sale_date = CURDATE()`
    );
    const data = rows[0] || { count: 0, total: 0 };
    const total = parseFloat(data.total || 0) || 0;
    const count = parseInt(data.count || 0) || 0;
    return {
      text: `ဒီနေ့ ရောင်းအား ${count} မှတ်တမ်း၊ စုစုပေါင်းဝင်ငွေ ${Number(total).toLocaleString()} Ks ရှိပါတယ်`,
      text_en: `Today sales: ${count} transactions, total ${Number(total).toLocaleString()} Ks`,
      data: { total, count },
      speak: true,
    };
  },

  async todayReport() {
    const [sales, bookings, topups, members] = await Promise.all([
      queryDB(`SELECT COALESCE(SUM(net), 0) as total, COUNT(*) as count FROM sales_daily WHERE sale_date = CURDATE()`),
      queryDB(`SELECT COUNT(*) as count FROM console_booking WHERE booking_date = CURDATE()`),
      queryDB(`SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count FROM topup_log WHERE DATE(topup_date) = CURDATE()`),
      queryDB(`SELECT COUNT(*) as count FROM sales_daily WHERE sale_date = CURDATE() AND member_id IS NOT NULL AND member_id != ''`),
    ]);

    const s = sales[0] || { total: 0, count: 0 };
    const b = bookings[0] || { count: 0 };
    const t = topups[0] || { total: 0, count: 0 };
    const mc = members[0] || { count: 0 };

    const sTotal = parseFloat(s.total || 0) || 0;
    const tTotal = parseFloat(t.total || 0) || 0;
    const sCount = parseInt(s.count || 0) || 0;
    const bCount = parseInt(b.count || 0) || 0;
    const tCount = parseInt(t.count || 0) || 0;
    const mcCount = parseInt(mc.count || 0) || 0;
    const totalRev = sTotal + tTotal;

    return {
      text: `📊 PS VIBE ဒီနေ့စာရင်း\n` +
        `💰 ရောင်းအား: ${Number(sTotal).toLocaleString()} Ks (${sCount} မှတ်တမ်း)\n` +
        `🎮 Console ဘွတ်ကင်: ${bCount} ခု\n` +
        `📱 Top-up: ${Number(tTotal).toLocaleString()} Ks (${tCount} ခု)\n` +
        `👥 အဖွဲ့ဝင်လာရောက်: ${mcCount} ယောက်\n` +
        `💵 စုစုပေါင်း: ${Number(totalRev).toLocaleString()} Ks`,
      text_en: `📊 PS VIBE Today Report\n` +
        `Sales: ${Number(parseFloat(s.total)).toLocaleString()} Ks (${s.count} txn)\n` +
        `Bookings: ${b.count}\n` +
        `Top-ups: ${Number(parseFloat(t.total)).toLocaleString()} Ks (${t.count})\n` +
        `Members: ${mc.count}\n` +
        `Total Revenue: ${Number(totalRev).toLocaleString()} Ks`,
      data: {
        sales: { total: sTotal, count: sCount },
        bookings: { count: bCount },
        topups: { total: tTotal, count: tCount },
        members: mcCount,
        total_revenue: totalRev,
      },
      speak: true,
    };
  },

  async weekReport() {
    const [sales, bookings, topups] = await Promise.all([
      queryDB(
        `SELECT COALESCE(SUM(net), 0) as total, COUNT(*) as count FROM sales_daily WHERE sale_date >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY) AND sale_date <= CURDATE()`
      ),
      queryDB(
        `SELECT COUNT(*) as count FROM console_booking WHERE booking_date >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY) AND booking_date <= CURDATE()`
      ),
      queryDB(
        `SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count FROM topup_log WHERE DATE(topup_date) >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY) AND DATE(topup_date) <= CURDATE()`
      ),
    ]);

    const s = sales[0] || { total: 0, count: 0 };
    const b = bookings[0] || { count: 0 };
    const t = topups[0] || { total: 0, count: 0 };
    const sTotal = parseFloat(s.total || 0) || 0;
    const tTotal = parseFloat(t.total || 0) || 0;
    const sCount = parseInt(s.count || 0) || 0;
    const bCount = parseInt(b.count || 0) || 0;
    const tCount = parseInt(t.count || 0) || 0;
    const totalRev = sTotal + tTotal;

    return {
      text: `📊 PS VIBE ဒီအပတ်စာရင်း\n` +
        `💰 ရောင်းအား: ${Number(sTotal).toLocaleString()} Ks (${sCount} မှတ်တမ်း)\n` +
        `🎮 Console ဘွတ်ကင်: ${bCount} ခု\n` +
        `📱 Top-up: ${Number(tTotal).toLocaleString()} Ks (${tCount} ခု)\n` +
        `💵 စုစုပေါင်း: ${Number(totalRev).toLocaleString()} Ks`,
      text_en: `📊 PS VIBE This Week\n` +
        `Sales: ${Number(parseFloat(s.total)).toLocaleString()} Ks (${s.count} txn)\n` +
        `Bookings: ${b.count}\n` +
        `Top-ups: ${Number(parseFloat(t.total)).toLocaleString()} Ks (${t.count})\n` +
        `Total Revenue: ${Number(totalRev).toLocaleString()} Ks`,
      data: {
        sales: { total: parseFloat(s.total), count: s.count },
        bookings: { count: b.count },
        topups: { total: parseFloat(t.total), count: t.count },
        total_revenue: totalRev,
      },
      speak: true,
    };
  },

  async memberBalance(entities) {
    const memberId = entities.member_id;
    if (!memberId) {
      return { text: 'ကျေးဇူးပြု၍ member ID ထည့်ပါ။ ဥပမာ — "member PSV_A001 balance"', text_en: 'Please provide a member ID. Example: "member PSV_A001 balance"', speak: true };
    }

    const rows = await queryDB(
      `SELECT member_id, member_name, phone, balance_mins, total_spend, lifetime_spend, tier, join_date FROM member_wallets WHERE member_id = '${memberId}'`
    );

    if (rows.length === 0) {
      return {
        text: `အဖွဲ့ဝင် ${memberId} မတွေ့ပါ။ Member ID မှန်ကန်မှုစစ်ဆေးပါ။`,
        text_en: `Member ${memberId} not found. Please check the member ID.`,
        speak: true,
      };
    }

    const m = rows[0];
    return {
      text: `👤 အဖွဲ့ဝင်: ${m.member_name || memberId}\n` +
        `🆔 ID: ${m.member_id}\n` +
        `📞 ဖုန်း: ${m.phone || 'N/A'}\n` +
        `⏱️ လက်ကျန်: ${m.balance_mins || 0} မိနစ်\n` +
        `💰 သုံးငွေ: ${Number(parseFloat(m.total_spend || 0)).toLocaleString()} Ks\n` +
        `⭐ Tier: ${m.tier || 'Standard'}\n` +
        `📅 Join: ${m.join_date || 'N/A'}`,
      text_en: `👤 Member: ${m.member_name || memberId}\n` +
        `ID: ${m.member_id}\n` +
        `Phone: ${m.phone || 'N/A'}\n` +
        `Balance: ${m.balance_mins || 0} mins\n` +
        `Spend: ${Number(parseFloat(m.total_spend || 0)).toLocaleString()} Ks\n` +
        `Tier: ${m.tier || 'Standard'}\n` +
        `Joined: ${m.join_date || 'N/A'}`,
      data: m,
      speak: true,
    };
  },

  async consoleStatus() {
    const rows = await queryDB(
      `SELECT console_id, status, console_type, current_game, current_member FROM console_status ORDER BY console_id`
    );

    if (rows.length === 0) {
      return { text: 'Console အချက်အလက်မရှိသေးပါ။', text_en: 'No console data available.', speak: true };
    }

    const free = rows.filter(r => r.status && r.status.toLowerCase() === 'free').length;
    const busy = rows.length - free;

    let text = `🎮 PS VIBE Console Status\n` +
      `✅ Free: ${free} | 🔴 Busy: ${busy} | 📊 Total: ${rows.length}\n`;
    let text_en = `🎮 PS VIBE Console Status\n` +
      `✅ Free: ${free} | 🔴 Busy: ${busy} | 📊 Total: ${rows.length}\n`;

    for (const c of rows) {
      const statusIcon = c.status && c.status.toLowerCase() === 'free' ? '✅' : '🔴';
      const ct = (c.console_type || '').toLowerCase();
      const emoji = ct.includes('ps4') ? '🎮' : '🕹️';
      text += `${emoji} ${c.console_id || '?'}: ${statusIcon} ${c.status || 'unknown'}`;
      text_en += `${emoji} ${c.console_id || '?'}: ${statusIcon} ${c.status || 'unknown'}`;
      if (c.current_game) {
        text += ` — ${c.current_game}`;
        text_en += ` — ${c.current_game}`;
      }
      if (c.current_member) {
        text += ` (${c.current_member})`;
        text_en += ` (${c.current_member})`;
      }
      text += '\n';
      text_en += '\n';
    }

    return { text, text_en, data: { consoles: rows, free, busy, total: rows.length }, speak: true };
  },

  async todayCustomers() {
    const rows = await queryDB(
      `SELECT COUNT(DISTINCT member_id) as unique_members, COUNT(*) as total_visits FROM sales_daily WHERE sale_date = CURDATE() AND member_id IS NOT NULL AND member_id != ''`
    );
    const d = rows[0] || { unique_members: 0, total_visits: 0 };
    const um = parseInt(d.unique_members || 0) || 0;
    const tv = parseInt(d.total_visits || 0) || 0;
    return {
      text: `ဒီနေ့ အဖွဲ့ဝင် ${um} ယောက်လာရောက်ပါတယ် (စုစုပေါင်း ${tv} ခေါက်)`,
      text_en: `Today: ${um} unique members visited (${tv} total visits)`,
      data: { unique_members: um, total_visits: tv },
      speak: true,
    };
  },

  async topGames() {
    // Query from console_booking (game_name column + booking_date)
    let rows = [];
    try {
      rows = await queryDB(
        'SELECT game_name as game_title, COUNT(*) as play_count FROM console_booking WHERE game_name IS NOT NULL AND game_name != \"\" AND booking_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) GROUP BY game_name ORDER BY play_count DESC LIMIT 10'
      );
    } catch (e) {
      // Fallback to games_library
      try {
        rows = await queryDB(
          'SELECT game_title, disc_count as play_count FROM games_library ORDER BY disc_count DESC LIMIT 10'
        );
      } catch (e2) {
        rows = [];
      }
    }

    if (!rows || rows.length === 0) {
      return { text: 'ဂိမ်းကစားမှတ်တမ်းမရှိသေးပါ။', text_en: 'No game play history yet.', speak: true };
    }

    let text = '🎯 PS VIBE နာမည်ကြီးဂိမ်းများ (ရက် ၃၀)\n';
    let text_en = '🎯 PS VIBE Top Games (30 days)\n';
    rows.forEach((g, i) => {
      text += `${i + 1}. ${g.game_title} — ${g.play_count} ခေါက်\n`;
      text_en += `${i + 1}. ${g.game_title} — ${g.play_count} plays\n`;
    });

    return { text, text_en, data: rows, speak: true };
  },

  async inventoryLow() {
    const rows = await queryDB(
      `SELECT item_name, category, quantity, reorder_level, unit_price FROM inventory WHERE quantity <= reorder_level AND reorder_level > 0 ORDER BY quantity ASC`
    );

    if (rows.length === 0) {
      return { text: 'ကုန်ခါနီးပစ္စည်းမရှိပါ။ စတော့အားလုံးလုံလောက်ပါတယ် ✅', text_en: 'No low stock items. All inventory sufficient ✅', speak: true };
    }

    let text = '⚠️ ကုန်ခါနီးပစ္စည်းများ\n';
    let text_en = '⚠️ Low Stock Items\n';
    for (const item of rows) {
      text += `📦 ${item.item_name} — ${item.quantity} ခု (အနည်းဆုံး: ${item.reorder_level})\n`;
      text_en += `📦 ${item.item_name} — ${item.quantity} qty (min: ${item.reorder_level})\n`;
    }

    return { text, text_en, data: rows, speak: true };
  },

  async staffDuty() {
    const rows = await queryDB(
      `SELECT a.staff_id, s.staff_name, s.role, a.check_in, a.check_out, a.status, a.hours_worked
       FROM attendance_log a
       JOIN staff_records s ON a.staff_id = s.staff_id
       WHERE a.date = CURDATE() AND a.status = 'checked_in'
       ORDER BY a.check_in ASC`
    );

    if (rows.length === 0) {
      return { text: 'ဒီနေ့ တာဝန်ကျဝန်ထမ်းမရှိသေးပါ။', text_en: 'No staff checked in today.', speak: true };
    }

    let text = '👥 ဒီနေ့တာဝန်ကျဝန်ထမ်းများ\n';
    let text_en = '👥 Staff On Duty Today\n';
    for (const s of rows) {
      const checkIn = s.check_in ? new Date(s.check_in).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }) : 'N/A';
      const emoji = (s.role || '').toLowerCase().includes('admin') ? '👑' : '💼';
      text += `${emoji} ${s.staff_name} (${s.role || 'Staff'}) — ဝင်: ${checkIn}\n`;
      text_en += `${emoji} ${s.staff_name} (${s.role || 'Staff'}) — In: ${checkIn}\n`;
    }

    return { text, text_en, data: rows, speak: true };
  },

  async todayBookings() {
    const rows = await queryDB(
      `SELECT console_id, member_id, start_time, end_time, status, game_name, duration_mins
       FROM console_booking
       WHERE booking_date = CURDATE()
       ORDER BY start_time ASC`
    );

    if (rows.length === 0) {
      return { text: 'ဒီနေ့ဘွတ်ကင်မရှိသေးပါ။', text_en: 'No bookings today.', speak: true };
    }

    let text = '📅 ဒီနေ့ Console ဘွတ်ကင်များ\n';
    let text_en = '📅 Today\'s Console Bookings\n';
    for (const b of rows) {
      const start = b.start_time ? new Date(b.start_time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }) : 'N/A';
      const statusIcon = b.status === 'completed' ? '✅' : b.status === 'active' ? '🔴' : '⏳';
      text += `${statusIcon} ${b.console_id} — ${b.member_id || 'Walk-in'} | ${start} | ${b.duration_mins}min | ${b.game_name || '-'}\n`;
      text_en += `${statusIcon} ${b.console_id} — ${b.member_id || 'Walk-in'} | ${start} | ${b.duration_mins}min | ${b.game_name || '-'}\n`;
    }

    return { text, text_en, data: rows, speak: true };
  },

  async help() {
    const cmds = COMMANDS.filter(c => c.description);
    let text = '🤖 Kora Voice Assistant — မေးနိုင်သောအကြောင်းအရာများ\n\n';
    let text_en = '🤖 Kora Voice Assistant — Available Commands\n\n';
    for (const c of cmds) {
      text += `• ${c.description.split(' / ')[1] || c.description}\n`;
    }
    text += '\nမေးခွန်းကို မြန်မာလို (သို့) English လို ရိုက်ထည့်နိုင်ပါတယ်။';
    text_en += '\nYou can type questions in Burmese or English.';
    return { text, text_en, data: cmds.map(c => c.description), speak: true };
  },

  async unknown(text) {
    return {
      text: `မသိသောမေးခွန်းပါ။ "help" လို့ရိုက်ပြီး မေးနိုင်သောအကြောင်းအရာများကြည့်ပါ။\n\nမေးခွန်း: "${text}"`,
      text_en: `Unknown command. Type "help" to see available commands.\n\nQuery: "${text}"`,
      speak: true,
    };
  },
};

// =========================================================================
// Express Server
// =========================================================================

const app = express();
app.use(express.json());

// POST /command — Main command endpoint
app.post('/command', async (req, res) => {
  const { command, lang } = req.body || {};

  if (!command || !command.trim()) {
    return res.json({
      success: false,
      command: 'empty',
      text: 'ကျေးဇူးပြု၍ မေးခွန်းထည့်ပါ။',
      text_en: 'Please enter a command.',
      error: 'empty_command',
    });
  }

  try {
    const parsed = parseCommand(command.trim());
    const result = await handlers[parsed.handler](parsed.entities, command.trim());

    const response = {
      success: true,
      command: parsed.handler,
      text: lang === 'en' && result.text_en ? result.text_en : result.text,
      text_en: result.text_en || result.text,
      speak: result.speak || false,
      data: result.data || null,
    };

    res.json(response);
  } catch (err) {
    console.error(`[Kora] Command error: ${err.message}`);
    res.json({
      success: false,
      command: 'error',
      text: `⚠️ Error: ${err.message}`,
      text_en: `⚠️ Error: ${err.message}`,
      error: err.message,
    });
  }
});

// POST /tts — TTS endpoint (marks text as speakable)
app.post('/tts', (req, res) => {
  const { text } = req.body || {};
  res.json({
    success: true,
    text: text || 'No text provided',
    speak: true,
    tts: true,
    voice: 'Nova',
  });
});

// GET /health — Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'kora-voice', timestamp: new Date().toISOString() });
});

// GET / — Simple welcome
app.get('/', (req, res) => {
  res.json({
    service: 'Kora Voice Assistant',
    version: '1.0.0',
    endpoints: {
      'POST /command': 'Process a voice/text command',
      'POST /tts': 'Text-to-speech marker',
      'GET /health': 'Health check',
    },
    examples: [
      'POST /command {"command": "ဒီနေ့ဝင်ငွေဘယ်လောက်လဲ"}',
      'POST /command {"command": "today sales"}',
      'POST /command {"command": "consoles status"}',
      'POST /command {"command": "member PSV_A001 balance"}',
    ],
  });
});

// Start server
app.listen(PORT, HOST, () => {
  console.log(`🎤 Kora Voice Assistant running on http://${HOST}:${PORT}`);
  console.log(`   Mode: ${SSH_HOST ? `SSH → ${SSH_HOST}` : (DIRECT_MYSQL || MYSQL_PASSWORD ? 'Direct MySQL' : '⚠️ No DB configured')}`);
  console.log(`   Endpoints: POST /command, POST /tts, GET /health`);
});

module.exports = { app, parseCommand, handlers, queryDB };
