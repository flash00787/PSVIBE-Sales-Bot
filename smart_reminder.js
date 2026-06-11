#!/usr/bin/env node
/**
 * ⏰ Smart Reminder System — Kora Workspace
 *
 * Cron-based reminders for:
 *   - Session end timers (console sessions running too long)
 *   - Member balance low warnings
 *   - Birthday greetings (staff + members)
 *   - Booking reminders (10min before)
 *   - Recurring (daily/weekly) + One-shot modes
 *
 * Run: node smart_reminder.js [check|add|list|remove|run]
 * Cron: every 15 minutes
 */

const { mysqlQuery } = require('./lib/ssh_vps');
const fs = require('fs');
const path = require('path');

const REMINDERS_FILE = path.join(__dirname, 'memory', 'reminders.json');
const REMINDER_LOG = path.join(__dirname, 'memory', 'reminder_log.jsonl');

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

function mmNow() {
  const now = new Date();
  now.setTime(now.getTime() + 6.5 * 3600000);
  return now;
}

function mmDate() {
  return mmNow().toISOString().split('T')[0];
}

function loadReminders() {
  try { return JSON.parse(fs.readFileSync(REMINDERS_FILE, 'utf8')); }
  catch { return { recurring: [], oneShot: [] }; }
}

function saveReminders(reminders) {
  fs.writeFileSync(REMINDERS_FILE, JSON.stringify(reminders, null, 2));
}

function logReminder(entry) {
  fs.appendFileSync(REMINDER_LOG, JSON.stringify({ ...entry, timestamp: new Date().toISOString() }) + '\n');
}

// ═══════════════════════════════════════════
// REMINDER TYPES
// ═══════════════════════════════════════════
const REMINDER_TYPES = {
  session_end: {
    name: 'Session End Timer',
    icon: '⏰',
    description: 'Warn when console session exceeds booked time',
  },
  low_balance: {
    name: 'Low Balance Alert',
    icon: '💰',
    description: 'Notify members when balance drops below threshold',
  },
  booking_reminder: {
    name: 'Booking Reminder',
    icon: '📅',
    description: 'Remind 10 min before console booking starts',
  },
  birthday: {
    name: 'Birthday Greeting',
    icon: '🎂',
    description: 'Send birthday wishes to staff/members',
  },
  custom: {
    name: 'Custom Reminder',
    icon: '📌',
    description: 'User-defined one-shot or recurring reminder',
  },
};

// ═══════════════════════════════════════════
// 1. SESSION END DETECTION
// ═══════════════════════════════════════════
async function checkSessionEndTimers() {
  const reminders = [];
  const consoles = parseTable(await mysqlQuery(
    "SELECT console_id, status, current_member, start_time FROM console_status WHERE status IN ('Occupied', 'Active') AND start_time IS NOT NULL"
  ));

  for (const c of consoles) {
    if (!c.start_time || c.start_time === 'NULL') continue;
    const startTime = new Date(c.start_time);
    const hoursElapsed = (mmNow().getTime() - startTime.getTime()) / 3600000;

    // Check if there's an active booking for this console
    const bookings = parseTable(await mysqlQuery(
      `SELECT id, end_time, duration_mins FROM console_booking 
       WHERE console_id = '${c.console_id}' AND status = 'confirmed'
       AND start_time <= NOW() AND end_time >= NOW()
       ORDER BY start_time DESC LIMIT 1`
    ));

    if (bookings.length > 0) {
      const b = bookings[0];
      const endTime = new Date(b.end_time);
      const minsLeft = Math.round((endTime.getTime() - mmNow().getTime()) / 60000);

      if (minsLeft <= 10 && minsLeft >= -5) {
        reminders.push({
          type: 'session_end',
          priority: 'high',
          message: `⏰ Console ${c.console_id}: Session ending in ${minsLeft} min (Member: ${c.current_member || '?'})`,
          consoleId: c.console_id,
          member: c.current_member,
          minsLeft,
        });
      } else if (minsLeft < -5) {
        reminders.push({
          type: 'session_end',
          priority: 'critical',
          message: `🔴 Console ${c.console_id}: OVERTIME by ${Math.abs(minsLeft)} min (Member: ${c.current_member || '?'})`,
          consoleId: c.console_id,
          member: c.current_member,
          minsOvertime: Math.abs(minsLeft),
        });
      }
    } else if (hoursElapsed > 3) {
      // No booking but console occupied > 3 hours
      reminders.push({
        type: 'session_end',
        priority: 'medium',
        message: `⚠️ Console ${c.console_id}: Occupied ${hoursElapsed.toFixed(1)}h without booking (${c.current_member || '?'})`,
        consoleId: c.console_id,
        hoursElapsed: hoursElapsed.toFixed(1),
      });
    }
  }

  return reminders;
}

// ═══════════════════════════════════════════
// 2. LOW BALANCE CHECK
// ═══════════════════════════════════════════
async function checkLowBalances(threshold = 30) {
  const reminders = [];

  const lowMembers = parseTable(await mysqlQuery(
    `SELECT member_id, member_name, balance_mins, phone FROM member_wallets 
     WHERE balance_mins < ${threshold} AND balance_mins > 0
     ORDER BY balance_mins ASC LIMIT 10`
  ));

  for (const m of lowMembers) {
    reminders.push({
      type: 'low_balance',
      priority: m.balance_mins < 10 ? 'high' : 'medium',
      message: `💰 ${m.member_name || m.member_id}: Only ${m.balance_mins} mins left`,
      memberId: m.member_id,
      memberName: m.member_name,
      balanceMins: parseInt(m.balance_mins),
    });
  }

  return reminders;
}

// ═══════════════════════════════════════════
// 3. BIRTHDAY CHECK
// ═══════════════════════════════════════════
async function checkBirthdays() {
  const reminders = [];
  const todayMM = mmDate();
  const todayMD = todayMM.slice(5); // MM-DD

  // Check staff_records for birthdays — we check members and staff
  // Staff records don't have birthday field directly, use members or staff_records
  // For now, check from a hypothetical birthday field or use custom reminders

  // Check if there are birthday reminders registered manually
  const storedReminders = loadReminders();
  const birthdayReminders = storedReminders.recurring.filter(r =>
    r.type === 'birthday' && r.date === todayMD
  );

  for (const br of birthdayReminders) {
    reminders.push({
      type: 'birthday',
      priority: 'high',
      message: `🎂 Happy Birthday to ${br.targetName || br.targetId}! 🎉`,
      targetId: br.targetId,
      targetName: br.targetName,
    });
  }

  return reminders;
}

// ═══════════════════════════════════════════
// 4. BOOKING REMINDER (10 min before)
// ═══════════════════════════════════════════
async function checkBookingReminders() {
  const reminders = [];
  const now = mmNow();
  const in15min = new Date(now.getTime() + 15 * 60000);

  const bookings = parseTable(await mysqlQuery(
    `SELECT id, console_id, member_id, start_time, end_time, telegram_chat_id, phone
     FROM console_booking 
     WHERE status IN ('confirmed', 'pending')
     AND start_time BETWEEN '${now.toISOString().replace('T',' ').slice(0,19)}' 
                        AND '${in15min.toISOString().replace('T',' ').slice(0,19)}'
     ORDER BY start_time`
  ));

  for (const b of bookings) {
    const minsUntil = Math.round((new Date(b.start_time).getTime() - now.getTime()) / 60000);
    reminders.push({
      type: 'booking_reminder',
      priority: 'high',
      message: `📅 Booking #${b.id}: Console ${b.console_id} starts in ${minsUntil} min — Member: ${b.member_id || '?'}`,
      bookingId: b.id,
      consoleId: b.console_id,
      memberId: b.member_id,
      minsUntil,
      phone: b.phone,
      telegramChatId: b.telegram_chat_id,
    });
  }

  return reminders;
}

// ═══════════════════════════════════════════
// 5. CUSTOM REMINDERS
// ═══════════════════════════════════════════
async function checkCustomReminders() {
  const reminders = [];
  const stored = loadReminders();
  const now = mmNow();
  const today = mmDate();
  const nowTime = now.toTimeString().slice(0, 5);

  // One-shot reminders due now
  const dueOneShots = stored.oneShot.filter(r => {
    if (r.fired) return false;
    const trigger = new Date(r.triggerAt);
    return trigger <= now;
  });

  for (const r of dueOneShots) {
    reminders.push({
      type: 'custom',
      priority: r.priority || 'medium',
      message: `📌 ${r.message}`,
      customId: r.id,
    });
    r.fired = true;
    r.firedAt = new Date().toISOString();
  }

  // Recurring reminders
  const dueRecurring = stored.recurring.filter(r => {
    if (!r.enabled) return false;
    // Check date
    if (r.date && r.date !== today) return false;
    // Check time
    if (r.time && r.time !== nowTime) return false;
    // Check day of week
    if (r.dayOfWeek !== undefined) {
      const dow = now.getDay(); // 0=Sun
      if (dow !== r.dayOfWeek) return false;
    }
    return true;
  });

  for (const r of dueRecurring) {
    reminders.push({
      type: 'custom',
      priority: r.priority || 'medium',
      message: `📌 [Recurring] ${r.message}`,
      customId: r.id,
      recurring: true,
    });
    // Update last triggered
    r.lastTriggered = new Date().toISOString();
  }

  saveReminders(stored);
  return reminders;
}

// ═══════════════════════════════════════════
// MAIN: RUN ALL REMINDER CHECKS
// ═══════════════════════════════════════════
async function runAllChecks() {
  console.log('⏰ Smart Reminder System — Running checks...\n');

  const allReminders = [];

  // 1. Session end timers
  try {
    const sessions = await checkSessionEndTimers();
    allReminders.push(...sessions);
    console.log(`  🎮 Sessions: ${sessions.length} reminders`);
  } catch (e) {
    console.error(`  ❌ Session check failed: ${e.message}`);
  }

  // 2. Low balances
  try {
    const balances = await checkLowBalances(30);
    allReminders.push(...balances);
    console.log(`  💰 Balances: ${balances.length} low balance alerts`);
  } catch (e) {
    console.error(`  ❌ Balance check failed: ${e.message}`);
  }

  // 3. Birthdays
  try {
    const birthdays = await checkBirthdays();
    allReminders.push(...birthdays);
    console.log(`  🎂 Birthdays: ${birthdays.length} today`);
  } catch (e) {
    console.error(`  ❌ Birthday check failed: ${e.message}`);
  }

  // 4. Booking reminders
  try {
    const bookingAlerts = await checkBookingReminders();
    allReminders.push(...bookingAlerts);
    console.log(`  📅 Bookings: ${bookingAlerts.length} upcoming`);
  } catch (e) {
    console.error(`  ❌ Booking check failed: ${e.message}`);
  }

  // 5. Custom reminders
  try {
    const customs = await checkCustomReminders();
    allReminders.push(...customs);
    console.log(`  📌 Custom: ${customs.length} due`);
  } catch (e) {
    console.error(`  ❌ Custom check failed: ${e.message}`);
  }

  // Log all
  for (const r of allReminders) {
    logReminder(r);
  }

  // Summary
  const highPriority = allReminders.filter(r => r.priority === 'high' || r.priority === 'critical');
  console.log(`\n📊 Total reminders: ${allReminders.length} (${highPriority.length} high priority)`);

  if (highPriority.length > 0) {
    console.log('\n🚨 HIGH PRIORITY:');
    highPriority.forEach(r => console.log(`  ${r.message}`));
  }

  return allReminders;
}

// ═══════════════════════════════════════════
// MANAGEMENT: ADD / LIST / REMOVE REMINDERS
// ═══════════════════════════════════════════
function addReminder(args) {
  const type = args[0];
  const message = args[1];
  const triggerAt = args[2]; // ISO datetime or cron-like

  if (!message) {
    console.log('Usage: node smart_reminder.js add <message> <triggerAt> [--recurring <daily|weekly|cron>]');
    return;
  }

  const reminders = loadReminders();

  if (triggerAt) {
    // One-shot
    reminders.oneShot.push({
      id: `rem_${Date.now()}`,
      type: 'custom',
      message,
      triggerAt,
      priority: 'medium',
      fired: false,
      createdAt: new Date().toISOString(),
    });
  } else {
    // Just store for next check
    reminders.oneShot.push({
      id: `rem_${Date.now()}`,
      type: 'custom',
      message,
      triggerAt: new Date().toISOString(), // Now
      priority: 'medium',
      fired: false,
      createdAt: new Date().toISOString(),
    });
  }

  saveReminders(reminders);
  console.log(`✅ Reminder added: "${message}"`);
}

function listReminders() {
  const reminders = loadReminders();
  console.log('📋 Reminders:\n');

  console.log('🔄 Recurring:');
  if (reminders.recurring.length === 0) console.log('  (none)');
  for (const r of reminders.recurring) {
    console.log(`  ${r.id} | ${r.type || 'custom'} | ${r.message?.substring(0, 60)} | ${r.enabled ? '✅' : '⏸️'}`);
  }

  console.log('\n📌 One-Shot:');
  const active = reminders.oneShot.filter(r => !r.fired);
  const fired = reminders.oneShot.filter(r => r.fired);
  console.log(`  Active: ${active.length}, Fired: ${fired.length}`);
  for (const r of active.slice(0, 10)) {
    console.log(`  ${r.id} | "${r.message?.substring(0, 60)}" | ${r.triggerAt}`);
  }
}

function removeReminder(id) {
  if (!id) { console.log('Usage: node smart_reminder.js remove <id>'); return; }
  const reminders = loadReminders();
  const before = reminders.oneShot.length + reminders.recurring.length;
  reminders.oneShot = reminders.oneShot.filter(r => r.id !== id);
  reminders.recurring = reminders.recurring.filter(r => r.id !== id);
  const after = reminders.oneShot.length + reminders.recurring.length;
  saveReminders(reminders);
  console.log(`🗑️  Removed ${before - after} reminder(s)`);
}

// ═══════════════════════════════════════════
// CLI
// ═══════════════════════════════════════════
async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0] || 'help';

  switch (cmd) {
    case 'check':
    case 'run': {
      const result = await runAllChecks();
      console.log(`\n✅ Reminder check complete — ${result.length} reminders`);
      break;
    }
    case 'add': {
      addReminder(args.slice(1));
      break;
    }
    case 'list': {
      listReminders();
      break;
    }
    case 'remove':
    case 'delete': {
      removeReminder(args[1]);
      break;
    }
    case 'types': {
      console.log('📋 Reminder Types:');
      for (const [key, t] of Object.entries(REMINDER_TYPES)) {
        console.log(`  ${t.icon} ${t.name}: ${t.description}`);
      }
      break;
    }
    default:
      console.log(`⏰ Smart Reminder System — Kora Workspace
═══════════════════════════════════════════
Commands:
  run / check     — Run all reminder checks now
  list            — List stored reminders
  add <msg> <at>  — Add a reminder (at = ISO datetime)
  remove <id>     — Remove a reminder
  types           — List reminder types

Auto-checks on each run:
  🎮 Session end timers (overtime detection)
  💰 Low balance alerts (< 30 mins)
  🎂 Birthday greetings (daily)
  📅 Booking reminders (15 min before)
  📌 Custom one-shot + recurring reminders

Run every 15 min via cron for best results.`);
  }
}

main().catch(e => {
  console.error('❌ Error:', e.message);
  process.exit(1);
});
