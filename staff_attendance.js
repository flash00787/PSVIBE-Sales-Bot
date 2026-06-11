#!/usr/bin/env node
/**
 * PS VIBE — Staff Attendance System
 * =================================
 * Check-in/check-out tracking, daily/monthly salary calculation.
 * 
 * Usage:
 *   node staff_attendance.js checkin <staff_id>
 *   node staff_attendance.js checkout <staff_id>
 *   node staff_attendance.js attendance [date|today|YYYY-MM-DD]
 *   node staff_attendance.js salary <staff_id> [start_date] [end_date]
 *   node staff_attendance.js status [staff_id]
 *   node staff_attendance.js staff-list
 *   node staff_attendance.js server [port]
 */

const mysql = require('mysql2/promise');
const http = require('http');

// ═══════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════
const DB_CONFIG = {
  host: '127.0.0.1',
  port: 3306,
  user: 'root',
  password: 'PsVibe@MySQL2024!',
  database: 'psvibe_api',
  charset: 'utf8mb4',
  connectTimeout: 10000,
};

const WORKING_HOURS_PER_DAY = 8;
const WORKING_DAYS_PER_MONTH = 26;

// ═══════════════════════════════════════════
// DATABASE HELPERS
// ═══════════════════════════════════════════

let pool = null;

async function getPool() {
  if (!pool) {
    pool = mysql.createPool(DB_CONFIG);
  }
  return pool;
}

async function query(sql, params = []) {
  const p = await getPool();
  const [rows] = await p.execute(sql, params);
  return rows;
}

async function getStaff(staffId) {
  const rows = await query(
    'SELECT staff_id, staff_name, base_salary, hourly_rate, role, is_active FROM staff_records WHERE staff_id = ?',
    [staffId]
  );
  return rows[0] || null;
}

async function getAllStaff() {
  return await query(
    'SELECT staff_id, staff_name, base_salary, hourly_rate, role, is_active FROM staff_records ORDER BY staff_id'
  );
}

// ═══════════════════════════════════════════
// CORE FUNCTIONS
// ═══════════════════════════════════════════

/**
 * Get current date/time in Asia/Yangon timezone (UTC+6:30)
 * Returns a Date-like object where getHours() etc return MMT values
 */
function mmtNow() {
  const now = new Date();
  const mmtOffset = 6.5 * 60 * 60 * 1000;
  return new Date(now.getTime() + mmtOffset);
}

function formatDateTime(d) {
  // d is already in MMT (either from mmtNow() or read from MySQL which stores MMT)
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, '0');
  const day = String(d.getUTCDate()).padStart(2, '0');
  const h = String(d.getUTCHours()).padStart(2, '0');
  const min = String(d.getUTCMinutes()).padStart(2, '0');
  const s = String(d.getUTCSeconds()).padStart(2, '0');
  return `${y}-${m}-${day} ${h}:${min}:${s}`;
}

function formatDate(d) {
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, '0');
  const day = String(d.getUTCDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/**
 * Format a MySQL datetime (stored as MMT) for display.
 * MySQL stores 'YYYY-MM-DD HH:MM:SS' as MMT but JavaScript Date parses it as UTC.
 * So we just format it directly without offset.
 */
function formatMySQLDateTime(mysqlDate) {
  if (!mysqlDate) return '—';
  // mysqlDate is a JS Date that parses the stored MMT string as if it were UTC
  // So getUTC* gives us the actual MMT time values
  const y = mysqlDate.getUTCFullYear();
  const m = String(mysqlDate.getUTCMonth() + 1).padStart(2, '0');
  const day = String(mysqlDate.getUTCDate()).padStart(2, '0');
  const h = String(mysqlDate.getUTCHours()).padStart(2, '0');
  const min = String(mysqlDate.getUTCMinutes()).padStart(2, '0');
  const s = String(mysqlDate.getUTCSeconds()).padStart(2, '0');
  return `${y}-${m}-${day} ${h}:${min}:${s}`;
}

/**
 * CHECK-IN: Record staff check-in time
 */
async function checkIn(staffId) {
  const staff = await getStaff(staffId);
  if (!staff) {
    return { success: false, message: `❌ Staff ID ${staffId} not found.` };
  }
  if (!staff.is_active) {
    return { success: false, message: `❌ ${staff.staff_name} is inactive.` };
  }

  const now = mmtNow();
  const today = formatDate(now);

  // Check if already checked in today without checkout
  const existing = await query(
    'SELECT id, check_in, status FROM attendance_log WHERE staff_id = ? AND date = ? ORDER BY id DESC LIMIT 1',
    [staffId, today]
  );

  if (existing.length > 0 && existing[0].status === 'checked_in') {
    return {
      success: false,
      message: `⚠️ ${staff.staff_name} already checked in at ${formatMySQLDateTime(existing[0].check_in)} MMT today. Use /checkout first.`
    };
  }

  await query(
    'INSERT INTO attendance_log (staff_id, check_in, date, status, hourly_rate) VALUES (?, ?, ?, ?, ?)',
    [staffId, formatDateTime(now), today, 'checked_in', staff.hourly_rate]
  );

  return {
    success: true,
    message: `✅ *${staff.staff_name}* checked in!\n🕐 Time: ${formatDateTime(now)} MMT\n📅 Date: ${today}\n💰 Rate: ${Number(staff.hourly_rate).toLocaleString()} Ks/hr`,
    staff_name: staff.staff_name,
    staff_id: staffId,
    check_in: formatDateTime(now),
    date: today,
  };
}

/**
 * CHECK-OUT: Record staff check-out and calculate pay
 */
async function checkOut(staffId) {
  const staff = await getStaff(staffId);
  if (!staff) {
    return { success: false, message: `❌ Staff ID ${staffId} not found.` };
  }

  const now = mmtNow();
  const today = formatDate(now);

  // Find today's open check-in
  const rows = await query(
    'SELECT id, check_in FROM attendance_log WHERE staff_id = ? AND date = ? AND status = ? ORDER BY id DESC LIMIT 1',
    [staffId, today, 'checked_in']
  );

  if (rows.length === 0) {
    return {
      success: false,
      message: `⚠️ ${staff.staff_name} has no active check-in for today. Use /checkin first.`
    };
  }

  const record = rows[0];
  // MySQL stores MMT datetime strings; JS Date parses them as UTC
  // So the raw Date values represent MMT when read with getUTC* methods
  const checkInTimeMs = record.check_in.getTime();
  const checkOutTimeMs = now.getTime(); // mmtNow() returns Date shifted by +6:30
  const diffMs = checkOutTimeMs - checkInTimeMs;
  const hoursWorked = Math.round((diffMs / (1000 * 60 * 60)) * 100) / 100;
  const hourlyRate = Number(staff.hourly_rate) || (Number(staff.base_salary) / WORKING_DAYS_PER_MONTH / WORKING_HOURS_PER_DAY);
  const dailyPay = Math.round(hoursWorked * hourlyRate);

  await query(
    'UPDATE attendance_log SET check_out = ?, hours_worked = ?, daily_pay = ?, status = ? WHERE id = ?',
    [formatDateTime(now), hoursWorked, dailyPay, 'completed', record.id]
  );

  return {
    success: true,
    message: `✅ *${staff.staff_name}* checked out!\n\n` +
      `🕐 In: ${formatMySQLDateTime(record.check_in)} MMT\n` +
      `🕐 Out: ${formatDateTime(now)} MMT\n` +
      `⏱️ Hours: ${hoursWorked.toFixed(2)}\n` +
      `💰 Rate: ${Number(hourlyRate).toLocaleString()} Ks/hr\n` +
      `💵 Today's Pay: ${dailyPay.toLocaleString()} Ks`,
    staff_name: staff.staff_name,
    staff_id: staffId,
    check_in: formatMySQLDateTime(record.check_in),
    check_out: formatDateTime(now),
    hours_worked: hoursWorked,
    daily_pay: dailyPay,
  };
}

/**
 * ATTENDANCE: Show attendance for a given date
 */
async function getAttendance(dateStr) {
  let targetDate;
  if (!dateStr || dateStr === 'today') {
    targetDate = formatDate(mmtNow());
  } else if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
    targetDate = dateStr;
  } else {
    return { success: false, message: '❌ Invalid date format. Use YYYY-MM-DD or "today".' };
  }

  const rows = await query(
    `SELECT a.id, a.staff_id, s.staff_name, a.check_in, a.check_out, 
            a.hours_worked, a.hourly_rate, a.daily_pay, a.status, a.notes
     FROM attendance_log a
     JOIN staff_records s ON a.staff_id = s.staff_id
     WHERE a.date = ?
     ORDER BY a.check_in ASC`,
    [targetDate]
  );

  if (rows.length === 0) {
    return { success: true, date: targetDate, records: [], message: `📅 *${targetDate}*\n\nNo attendance records found.` };
  }

  const lines = [`📅 *Attendance — ${targetDate}*`, '━━━━━━━━━━━━━━━━━━'];
  let totalPay = 0;

  for (const r of rows) {
    const checkIn = formatMySQLDateTime(r.check_in);
    const checkOut = formatMySQLDateTime(r.check_out);
    const hours = r.hours_worked ? Number(r.hours_worked).toFixed(2) : '—';
    const pay = Number(r.daily_pay) || 0;
    totalPay += pay;
    const statusIcon = r.status === 'checked_in' ? '🟢' : r.status === 'completed' ? '✅' : '⚠️';

    lines.push(
      `${statusIcon} *${r.staff_name}* (ID:${r.staff_id})`,
      `   In: ${checkIn}  Out: ${checkOut}`,
      `   Hours: ${hours}  |  Pay: ${pay.toLocaleString()} Ks`
    );
  }

  lines.push('━━━━━━━━━━━━━━━━━━');
  lines.push(`💵 *Total: ${totalPay.toLocaleString()} Ks*`);
  lines.push(`👥 Staff: ${rows.length}  |  🟢 Active: ${rows.filter(r => r.status === 'checked_in').length}`);

  return { success: true, date: targetDate, records: rows, message: lines.join('\n'), total_pay: totalPay };
}

/**
 * SALARY: Calculate salary for a staff member over a date range
 */
async function calcSalary(staffId, startDate, endDate) {
  const staff = await getStaff(staffId);
  if (!staff) {
    return { success: false, message: `❌ Staff ID ${staffId} not found.` };
  }

  // Default to this month if no dates given
  if (!startDate) {
    const now = mmtNow();
    startDate = `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, '0')}-01`;
    endDate = formatDate(now);
  } else if (!endDate) {
    endDate = startDate; // Single day
  }

  const rows = await query(
    `SELECT date, check_in, check_out, hours_worked, daily_pay, status
     FROM attendance_log
     WHERE staff_id = ? AND date >= ? AND date <= ? AND status = 'completed'
     ORDER BY date ASC`,
    [staffId, startDate, endDate]
  );

  if (rows.length === 0) {
    return {
      success: true,
      staff_name: staff.staff_name,
      period: `${startDate} → ${endDate}`,
      records: [],
      message: `📊 *${staff.staff_name}* — Salary Report\n📅 ${startDate} → ${endDate}\n\nNo completed attendance records found.`
    };
  }

  let totalHours = 0;
  let totalPay = 0;
  const detailLines = [];

  for (const r of rows) {
    const hours = Number(r.hours_worked) || 0;
    const pay = Number(r.daily_pay) || 0;
    totalHours += hours;
    totalPay += pay;
    const dateStr = typeof r.date === 'string' ? r.date : r.date.toISOString().split('T')[0];
    detailLines.push(`  ${dateStr}: ${hours.toFixed(2)}h — ${pay.toLocaleString()} Ks`);
  }

  const avgHoursPerDay = totalHours / rows.length;
  const workingDays = rows.length;

  const message = [
    `📊 *${staff.staff_name}* — Salary Report`,
    `━━━━━━━━━━━━━━━━━━`,
    `📅 Period: ${startDate} → ${endDate}`,
    `👤 Staff ID: ${staffId}`,
    `💰 Rate: ${Number(staff.hourly_rate || 0).toLocaleString()} Ks/hr`,
    `💰 Monthly Base: ${Number(staff.base_salary).toLocaleString()} Ks`,
    `━━━━━━━━━━━━━━━━━━`,
    `📋 Details:`,
    ...detailLines,
    `━━━━━━━━━━━━━━━━━━`,
    `📅 Working Days: ${workingDays}`,
    `⏱️ Total Hours: ${totalHours.toFixed(2)}`,
    `📊 Avg Hrs/Day: ${avgHoursPerDay.toFixed(2)}`,
    `💵 *Total Pay: ${totalPay.toLocaleString()} Ks*`,
  ].join('\n');

  return {
    success: true,
    staff_name: staff.staff_name,
    staff_id: staffId,
    period: { start: startDate, end: endDate },
    working_days: workingDays,
    total_hours: totalHours,
    total_pay: totalPay,
    records: rows,
    message,
  };
}

/**
 * STATUS: Check current check-in status for a staff member
 */
async function getStatus(staffId) {
  const staff = await getStaff(staffId);
  if (!staff) {
    return { success: false, message: `❌ Staff ID ${staffId} not found.` };
  }

  const today = formatDate(mmtNow());
  const rows = await query(
    'SELECT id, check_in, check_out, hours_worked, daily_pay, status FROM attendance_log WHERE staff_id = ? AND date = ? ORDER BY id DESC LIMIT 1',
    [staffId, today]
  );

  if (rows.length === 0) {
    return {
      success: true,
      staff_name: staff.staff_name,
      status: 'not_checked_in',
      message: `👤 *${staff.staff_name}* (ID:${staffId})\n📅 ${today}\n\n❌ Not checked in today.`
    };
  }

  const r = rows[0];
  const statusIcon = r.status === 'checked_in' ? '🟢 Working' : '✅ Completed';
  const checkIn = formatMySQLDateTime(r.check_in);
  let msg = `👤 *${staff.staff_name}* (ID:${staffId})\n📅 ${today}\n\n🕐 In: ${checkIn} MMT\n📌 Status: ${statusIcon}`;

  if (r.status === 'completed') {
    const checkOut = formatMySQLDateTime(r.check_out);
    msg += `\n🕐 Out: ${checkOut} MMT\n⏱️ Hours: ${Number(r.hours_worked).toFixed(2)}\n💵 Pay: ${Number(r.daily_pay).toLocaleString()} Ks`;
  }

  return { success: true, staff_name: staff.staff_name, status: r.status, record: r, message: msg };
}

// ═══════════════════════════════════════════
// HTTP SERVER MODE (for bot/webhook integration)
// ═══════════════════════════════════════════

function startServer(port = 3099) {
  const server = http.createServer(async (req, res) => {
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Access-Control-Allow-Origin', '*');

    if (req.method === 'OPTIONS') {
      res.writeHead(200);
      res.end('{}');
      return;
    }

    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      let params = {};
      try { params = JSON.parse(body || '{}'); } catch (e) { /* ignore */ }

      // Also parse query string
      const url = new URL(req.url, `http://localhost:${port}`);
      for (const [k, v] of url.searchParams) {
        params[k] = v;
      }

      const action = params.action || url.pathname.replace('/', '');
      let result;

      try {
        switch (action) {
          case 'checkin':
            result = await checkIn(parseInt(params.staff_id));
            break;
          case 'checkout':
            result = await checkOut(parseInt(params.staff_id));
            break;
          case 'attendance':
            result = await getAttendance(params.date || 'today');
            break;
          case 'salary':
            result = await calcSalary(parseInt(params.staff_id), params.start_date, params.end_date);
            break;
          case 'status':
            if (params.staff_id) {
              result = await getStatus(parseInt(params.staff_id));
            } else {
              const staff = await getAllStaff();
              const lines = [];
              for (const s of staff) {
                const r = await getStatus(s.staff_id);
                lines.push(r.message);
                lines.push('');
              }
              result = { success: true, message: lines.join('\n').trim() };
            }
            break;
          case 'staff-list':
            result = { success: true, staff: await getAllStaff() };
            break;
          case 'health':
            result = { success: true, status: 'ok', timestamp: formatDateTime(mmtNow()) };
            break;
          default:
            result = { success: false, message: `Unknown action: ${action}` };
        }
      } catch (e) {
        result = { success: false, message: e.message, stack: e.stack };
      }

      res.writeHead(result.success ? 200 : 400);
      res.end(JSON.stringify(result, null, 2));
    });
  });

  server.listen(port, '127.0.0.1', () => {
    console.log(`✅ Staff Attendance HTTP server running on http://127.0.0.1:${port}`);
    console.log(`   Endpoints: /checkin, /checkout, /attendance, /salary, /status, /staff-list`);
  });

  return server;
}

// ═══════════════════════════════════════════
// CLI MODE
// ═══════════════════════════════════════════

async function cliMain() {
  const args = process.argv.slice(2);
  const command = (args[0] || '').toLowerCase();

  try {
    let result;
    switch (command) {
      case 'checkin':
        result = await checkIn(parseInt(args[1]));
        break;
      case 'checkout':
        result = await checkOut(parseInt(args[1]));
        break;
      case 'attendance':
        result = await getAttendance(args[1] || 'today');
        break;
      case 'salary':
        result = await calcSalary(parseInt(args[1]), args[2], args[3]);
        break;
      case 'status':
        if (args[1]) {
          result = await getStatus(parseInt(args[1]));
        } else {
          // Show all staff status
          const staff = await getAllStaff();
          const lines = [];
          for (const s of staff) {
            const r = await getStatus(s.staff_id);
            lines.push(r.message);
            lines.push('');
          }
          result = { success: true, message: lines.join('\n') };
        }
        break;
      case 'staff-list':
        const staff = await getAllStaff();
        const slines = ['👥 *Staff List*', '━━━━━━━━━━━━━━━━━━'];
        for (const s of staff) {
          slines.push(`ID:${s.staff_id}  ${s.is_active ? '✅' : '❌'} ${s.staff_name} — ${Number(s.base_salary).toLocaleString()} Ks (${Number(s.hourly_rate).toLocaleString()} Ks/hr)`);
        }
        result = { success: true, message: slines.join('\n') };
        break;
      case 'server':
        const port = parseInt(args[1]) || 3099;
        startServer(port);
        // Keep alive
        process.stdin.resume();
        return; // Don't exit
      default:
        console.log([
          '📋 PS VIBE Staff Attendance System',
          '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━',
          'Usage: node staff_attendance.js <command> [args]',
          '',
          'Commands:',
          '  checkin <staff_id>          — Record check-in',
          '  checkout <staff_id>         — Record check-out',
          '  attendance [date]           — Show attendance (default: today)',
          '  salary <staff_id> [start] [end] — Calculate salary',
          '  status [staff_id]           — Check current status',
          '  staff-list                  — List all staff',
          '  server [port]               — Start HTTP server',
        ].join('\n'));
        process.exit(0);
    }

    if (result) {
      console.log(result.message || JSON.stringify(result, null, 2));
      if (!result.success) process.exit(1);
    }
  } catch (e) {
    console.error(`❌ Error: ${e.message}`);
    console.error(e.stack);
    process.exit(1);
  } finally {
    if (pool) await pool.end();
  }
}

// ═══════════════════════════════════════════
// MODULE EXPORTS (for require())
// ═══════════════════════════════════════════
module.exports = { checkIn, checkOut, getAttendance, calcSalary, getStatus, getAllStaff, startServer, mmtNow };

// ═══════════════════════════════════════════
// ENTRY POINT
// ═══════════════════════════════════════════
if (require.main === module) {
  cliMain().catch(e => {
    console.error('Fatal:', e.message);
    process.exit(1);
  });
}
