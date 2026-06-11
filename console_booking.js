#!/usr/bin/env node
/**
 * 🎮 Console Booking Auto-System — Kora Workspace
 *
 * Features:
 *   - Auto-suggest available time slots based on console_status + console_booking
 *   - Auto-reminder 10 min before booking
 *   - Cancellation auto-handler (release slot)
 *   - Conflict detection (no double-booking)
 *   - Daily booking summary
 *
 * Run: node console_booking.js [check|book|cancel|slots|remind|summary]
 *
 * Data source: MySQL via SSH (psvibe_api DB)
 */

const { mysqlQuery, sshExec } = require('./lib/ssh_vps');
const fs = require('fs');
const path = require('path');

const LOG_DIR = path.join(__dirname, 'memory', 'bookings');
if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });

// ═══════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════
function parseTable(output) {
  const lines = output.trim().split('\n');
  if (lines.length < 2) return [];
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

function mmTime() {
  const now = new Date();
  now.setTime(now.getTime() + 6.5 * 3600000);
  return now;
}

function fmtTime(iso) {
  if (!iso || iso === 'NULL') return '?';
  const d = new Date(iso);
  return d.toLocaleString('en-US', { timeZone: 'Asia/Yangon', hour12: false });
}

function todayYMD() {
  const mm = mmTime();
  return mm.toISOString().split('T')[0];
}

// ═══════════════════════════════════════════
// 1. GET AVAILABLE TIME SLOTS
// ═══════════════════════════════════════════
async function getAvailableSlots(date = null, consoleId = null) {
  const targetDate = date || todayYMD();

  // Get all consoles
  const consoles = parseTable(await mysqlQuery(
    'SELECT console_id, status, console_type FROM console_status ORDER BY console_id'
  ));

  // Get existing bookings for the date
  const bookings = parseTable(await mysqlQuery(
    `SELECT id, console_id, member_id, start_time, end_time, status, staff_name
     FROM console_booking 
     WHERE booking_date = '${targetDate}' AND status IN ('confirmed', 'pending')
     ORDER BY start_time`
  ));

  // Open hours: 10:00 - 22:00 Myanmar Time
  // Generate 1-hour slots for each console
  const slots = [];
  const openHour = 10;
  const closeHour = 22;

  for (const c of consoles) {
    if (consoleId && c.console_id !== consoleId) continue;

    for (let h = openHour; h < closeHour; h++) {
      const slotStart = new Date(`${targetDate}T${String(h).padStart(2, '0')}:00:00+06:30`);
      const slotEnd = new Date(`${targetDate}T${String(h + 1).padStart(2, '0')}:00:00+06:30`);

      // Check if slot is already booked
      const isBooked = bookings.some(b => {
        if (b.console_id !== c.console_id) return false;
        if (b.status === 'cancelled') return false;
        const bStart = new Date(b.start_time);
        const bEnd = new Date(b.end_time);
        // Overlap check
        return slotStart < bEnd && slotEnd > bStart;
      });

      slots.push({
        consoleId: c.console_id,
        consoleType: c.console_type,
        date: targetDate,
        startTime: slotStart.toISOString(),
        endTime: slotEnd.toISOString(),
        hour: h,
        available: !isBooked,
        status: isBooked ? 'booked' : 'available',
      });
    }
  }

  return { date: targetDate, consoles: consoles.length, slots, totalAvailable: slots.filter(s => s.available).length };
}

// ═══════════════════════════════════════════
// 2. CHECK BOOKING CONFLICTS
// ═══════════════════════════════════════════
async function checkBookingConflict(consoleId, startTime, endTime, excludeId = null) {
  const bookings = parseTable(await mysqlQuery(
    `SELECT id, console_id, start_time, end_time, status FROM console_booking
     WHERE console_id = '${consoleId}' AND status IN ('confirmed', 'pending')
     AND start_time < '${endTime}' AND end_time > '${startTime}'
     ${excludeId ? `AND id != ${excludeId}` : ''}`
  ));

  return bookings.length > 0 ? bookings : null;
}

// ═══════════════════════════════════════════
// 3. GET UPCOMING BOOKINGS (for reminders)
// ═══════════════════════════════════════════
async function getUpcomingBookings(minutesAhead = 15) {
  const now = mmTime();
  const future = new Date(now.getTime() + minutesAhead * 60000);

  const bookings = parseTable(await mysqlQuery(
    `SELECT id, console_id, member_id, start_time, end_time, status, staff_name, telegram_chat_id, phone, game_name
     FROM console_booking
     WHERE status IN ('confirmed', 'pending')
     AND start_time BETWEEN '${now.toISOString().replace('T', ' ').slice(0, 19)}' 
                        AND '${future.toISOString().replace('T', ' ').slice(0, 19)}'
     ORDER BY start_time`
  ));

  return bookings;
}

// ═══════════════════════════════════════════
// 4. CANCEL A BOOKING
// ═══════════════════════════════════════════
async function cancelBooking(bookingId) {
  const existing = parseTable(await mysqlQuery(
    `SELECT * FROM console_booking WHERE id = ${bookingId}`
  ));

  if (existing.length === 0) {
    return { success: false, error: `Booking #${bookingId} not found` };
  }

  const b = existing[0];

  // Update to cancelled
  await mysqlQuery(
    `UPDATE console_booking SET status = 'cancelled' WHERE id = ${bookingId}`
  );

  // Log
  const logEntry = {
    action: 'cancel',
    bookingId,
    consoleId: b.console_id,
    memberId: b.member_id,
    wasStartTime: b.start_time,
    cancelledAt: new Date().toISOString(),
  };
  fs.appendFileSync(
    path.join(LOG_DIR, 'cancellations.jsonl'),
    JSON.stringify(logEntry) + '\n'
  );

  return {
    success: true,
    booking: { id: bookingId, console_id: b.console_id, member_id: b.member_id },
    message: `✅ Booking #${bookingId} cancelled — Console ${b.console_id} released`,
  };
}

// ═══════════════════════════════════════════
// 5. AUTO-REMINDER CHECK
// ═══════════════════════════════════════════
async function checkReminders() {
  const upcoming = await getUpcomingBookings(15);

  if (upcoming.length === 0) {
    return { reminders: [], message: 'No upcoming bookings in the next 15 minutes' };
  }

  const reminders = upcoming.map(b => ({
    bookingId: b.id,
    consoleId: b.console_id,
    memberId: b.member_id,
    startTime: b.start_time,
    endTime: b.end_time,
    minutesUntil: Math.round((new Date(b.start_time).getTime() - mmTime().getTime()) / 60000),
    message: `⏰ Reminder: Booking #${b.id} for Console ${b.console_id} starts in ~${Math.round((new Date(b.start_time).getTime() - mmTime().getTime()) / 60000)} min`,
  }));

  return { reminders, count: reminders.length };
}

// ═══════════════════════════════════════════
// 6. DAILY BOOKING SUMMARY
// ═══════════════════════════════════════════
async function dailySummary(date = null) {
  const targetDate = date || todayYMD();

  const bookings = parseTable(await mysqlQuery(
    `SELECT id, console_id, member_id, start_time, end_time, status, staff_name, duration_mins
     FROM console_booking WHERE booking_date = '${targetDate}' ORDER BY start_time`
  ));

  // Summary by status
  const statusCount = {};
  const consoleUsage = {};
  let totalMins = 0;

  for (const b of bookings) {
    statusCount[b.status] = (statusCount[b.status] || 0) + 1;
    consoleUsage[b.console_id] = (consoleUsage[b.console_id] || 0) + (parseInt(b.duration_mins) || 60);
    totalMins += parseInt(b.duration_mins) || 60;
  }

  return {
    date: targetDate,
    total: bookings.length,
    byStatus: statusCount,
    byConsole: consoleUsage,
    totalMinutes: totalMins,
    totalHours: (totalMins / 60).toFixed(1),
    bookings,
  };
}

// ═══════════════════════════════════════════
// 7. CLEANUP OLD BOOKINGS
// ═══════════════════════════════════════════
async function cleanupOldBookings() {
  const yesterday = new Date(mmTime());
  yesterday.setDate(yesterday.getDate() - 1);
  const ymd = yesterday.toISOString().split('T')[0];

  // Cancel pending bookings from past dates
  await mysqlQuery(
    `UPDATE console_booking SET status = 'expired' 
     WHERE status = 'pending' AND booking_date < '${todayYMD()}'`
  );

  return { cleaned: true, message: 'Expired pending bookings cleaned up' };
}

// ═══════════════════════════════════════════
// MAIN CLI
// ═══════════════════════════════════════════
async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0] || 'help';

  console.log(`🎮 Console Booking Auto-System — ${new Date().toISOString()}\n`);

  switch (cmd) {
    case 'slots':
    case 'check': {
      const date = args[1] || null;
      const consoleId = args[2] || null;
      const result = await getAvailableSlots(date, consoleId);
      console.log(`📅 Date: ${result.date}`);
      console.log(`🎮 Consoles: ${result.consoles}`);
      console.log(`✅ Available slots: ${result.totalAvailable}/${result.slots.length}`);
      console.log(`\nHourly slots:`);
      // Group by console
      const byConsole = {};
      for (const s of result.slots) {
        if (!byConsole[s.consoleId]) byConsole[s.consoleId] = [];
        byConsole[s.consoleId].push(s);
      }
      for (const [cid, slots] of Object.entries(byConsole)) {
        console.log(`\n  🎮 ${cid} (${slots[0].consoleType}):`);
        for (const s of slots) {
          const icon = s.available ? '✅' : '🔴';
          const hh = String(s.hour).padStart(2, '0');
          console.log(`    ${icon} ${hh}:00 - ${String(s.hour+1).padStart(2,'0')}:00 (${s.available ? 'available' : 'booked'})`);
        }
      }
      break;
    }

    case 'remind': {
      const result = await checkReminders();
      console.log(`⏰ Reminder Check:`);
      console.log(`  Upcoming (next 15 min): ${result.count}`);
      for (const r of result.reminders) {
        console.log(`  🎮 ${r.message}`);
      }
      if (result.count === 0) console.log('  No upcoming bookings');
      break;
    }

    case 'cancel': {
      const bookingId = parseInt(args[1]);
      if (!bookingId) { console.log('❌ Usage: node console_booking.js cancel <bookingId>'); break; }
      const result = await cancelBooking(bookingId);
      console.log(result.success ? result.message : `❌ ${result.error}`);
      break;
    }

    case 'summary': {
      const date = args[1] || null;
      const result = await dailySummary(date);
      console.log(`📊 Booking Summary — ${result.date}`);
      console.log(`  Total bookings: ${result.total}`);
      console.log(`  Total hours: ${result.totalHours}`);
      console.log(`  Status:`, JSON.stringify(result.byStatus));
      console.log(`  Console usage:`, JSON.stringify(result.byConsole));
      if (result.bookings.length > 0) {
        console.log(`\n  Bookings:`);
        for (const b of result.bookings.slice(0, 10)) {
          console.log(`    #${b.id} | ${b.console_id} | ${b.member_id || '?'} | ${fmtTime(b.start_time)} → ${fmtTime(b.end_time)} | ${b.status}`);
        }
      }
      break;
    }

    case 'cleanup': {
      const result = await cleanupOldBookings();
      console.log(result.message);
      break;
    }

    default:
      console.log(`🎮 Console Booking Auto-System — Kora Workspace
═══════════════════════════════════════════
Commands:
  slots [date] [consoleId]  — Show available time slots
  remind                    — Check bookings starting in next 15 min
  cancel <bookingId>        — Cancel a booking
  summary [date]            — Daily booking summary
  cleanup                   — Auto-expire old pending bookings

Examples:
  node console_booking.js slots
  node console_booking.js slots 2026-06-11 C-01
  node console_booking.js remind
  node console_booking.js summary 2026-06-10`);
  }
}

main().catch(e => {
  console.error('❌ Error:', e.message);
  process.exit(1);
});
