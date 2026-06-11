#!/usr/bin/env node
/**
 * PS VIBE — Smart Inventory Alert System
 * Phase 5, Item 1: Monitors food/beverage stock, sends Telegram alerts,
 * suggests reorder quantities based on 7-day usage patterns.
 *
 * Usage:
 *   node inventory_alerts.js              # Check all items, alert if low
 *   node inventory_alerts.js --once       # Same as above (cron-friendly)
 *   node inventory_alerts.js --daily      # Daily summary for all items
 *   node inventory_alerts.js --test       # Test Telegram connectivity only
 *   node inventory_alerts.js --quiet      # Suppress non-alert console output
 *
 * Cron examples:
 *   # Check every 30 minutes:
 *   # *\/30 * * * * /usr/local/bin/node /opt/inventory_alerts/inventory_alerts.js --once >> /var/log/inventory_alerts.log 2>&1
 *   # Daily summary at 9 AM Yangon (2:30 UTC):
 *   # 30 2 * * * /usr/local/bin/node /opt/inventory_alerts/inventory_alerts.js --daily >> /var/log/inventory_alerts.log 2>&1
 */

const mysql = require('mysql2/promise');
const https = require('https');

// ── Configuration ────────────────────────────────────────────────────────────
const MYSQL_CFG = {
  host: process.env.MYSQL_HOST || '127.0.0.1',
  port: parseInt(process.env.MYSQL_PORT || '3306'),
  user: process.env.MYSQL_USER || 'psvibe_user',
  password: process.env.MYSQL_PASSWORD || 'PsVibe@2026_Rotated!',
  database: process.env.MYSQL_DATABASE || 'psvibe_api',
  connectTimeout: 10000,
};

const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || '8545665013:AAFgEuw4V_715Q9yzGOYloinIdbdYXYb8zU';
const STAFF_CHAT_ID = process.env.STAFF_NOTIFY_CHAT || '-1003686032747';
// Fallback: also send to boss directly
const BOSS_CHAT_ID = process.env.TELEGRAM_CHAT_ID || '6296803251';

// Default thresholds per category (used when reorder_level not set)
const DEFAULT_THRESHOLDS = {
  Drinks: 5,
  Snacks: 3,
  default: 3,
};

// Reorder multiplier: suggested reorder = daily_usage × DAYS_BUFFER
const DAYS_BUFFER = 7;

// ── CLI Args ─────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const FLAGS = {
  once: args.includes('--once') || args.includes('--daily') || args.length === 0,
  daily: args.includes('--daily'),
  test: args.includes('--test'),
  quiet: args.includes('--quiet'),
};

function log(msg) {
  if (!FLAGS.quiet) console.log(`[${new Date().toISOString()}] ${msg}`);
}

// ── MySQL Helpers ────────────────────────────────────────────────────────────

let pool = null;

async function getPool() {
  if (!pool) {
    pool = mysql.createPool({ ...MYSQL_CFG, waitForConnections: true, connectionLimit: 2 });
  }
  return pool;
}

async function query(sql, params = []) {
  const p = await getPool();
  const [rows] = await p.execute(sql, params);
  return rows;
}

// ── Telegram Alert ───────────────────────────────────────────────────────────

function sendTelegram(chatId, text) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      chat_id: chatId,
      text: text,
      parse_mode: 'HTML',
      disable_web_page_preview: true,
    });

    const url = new URL(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`);
    const options = {
      hostname: url.hostname,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
      timeout: 10000,
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', d => data += d);
      res.on('end', () => {
        if (res.statusCode === 200) {
          resolve(JSON.parse(data));
        } else {
          log(`Telegram API error ${res.statusCode}: ${data}`);
          reject(new Error(`Telegram API returned ${res.statusCode}`));
        }
      });
    });

    req.on('error', (e) => {
      log(`Telegram request failed: ${e.message}`);
      reject(e);
    });
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Telegram request timeout'));
    });

    req.write(body);
    req.end();
  });
}

async function alertStaff(text) {
  try {
    await sendTelegram(STAFF_CHAT_ID, text);
    log('Alert sent to staff group');
  } catch (e) {
    log(`Staff group alert failed (${e.message}), trying boss...`);
    try {
      await sendTelegram(BOSS_CHAT_ID, text);
      log('Alert sent to boss fallback');
    } catch (e2) {
      log(`Boss alert also failed: ${e2.message}`);
    }
  }
}

async function alertBoss(text) {
  try {
    await sendTelegram(BOSS_CHAT_ID, text);
    log('Sent to boss');
  } catch (e) {
    log(`Boss alert failed: ${e.message}`);
  }
}

// ── Core Logic ───────────────────────────────────────────────────────────────

/**
 * Get all inventory items with current stock levels
 */
async function getInventory() {
  return query(`
    SELECT id, item_name, category, quantity, unit_price, reorder_level, last_updated
    FROM inventory
    ORDER BY category, item_name
  `);
}

/**
 * Get 7-day sales (stock_out) for a specific item
 */
async function getItemUsage(itemName, days = 7) {
  const rows = await query(`
    SELECT 
      COUNT(*) as sale_count,
      COALESCE(SUM(quantity), 0) as total_sold,
      MAX(sale_date) as last_sale_date,
      DATEDIFF(CURDATE(), MIN(sale_date)) as active_days
    FROM stock_out
    WHERE item_name = ?
      AND sale_date >= DATE_SUB(CURDATE(), INTERVAL ? DAY)
  `, [itemName, days]);
  return rows[0] || { sale_count: 0, total_sold: 0, last_sale_date: null, active_days: 0 };
}

/**
 * Get last restock info for an item
 */
async function getLastRestock(itemName) {
  const rows = await query(`
    SELECT batch_id, quantity, unit_cost, total_cost, created_at
    FROM stock_in
    WHERE item_name = ?
    ORDER BY created_at DESC
    LIMIT 1
  `, [itemName]);
  return rows[0] || null;
}

/**
 * Get effective threshold for an item
 */
function getThreshold(item) {
  if (item.reorder_level && item.reorder_level > 0) return item.reorder_level;
  return DEFAULT_THRESHOLDS[item.category] || DEFAULT_THRESHOLDS.default;
}

/**
 * Calculate reorder suggestion
 */
function suggestReorder(currentQty, dailyUsage, threshold, unitPrice) {
  const rawReorder = Math.ceil(dailyUsage * DAYS_BUFFER);
  // Round up to common pack sizes
  let reorderQty = rawReorder;
  if (rawReorder <= 6) reorderQty = 6;
  else if (rawReorder <= 12) reorderQty = 12;
  else if (rawReorder <= 24) reorderQty = 24;
  else if (rawReorder <= 48) reorderQty = 48;
  else reorderQty = Math.ceil(rawReorder / 12) * 12;

  const estimatedCost = reorderQty * unitPrice;
  const daysUntilOut = dailyUsage > 0 ? Math.floor(currentQty / dailyUsage) : 999;

  return { reorderQty, estimatedCost, daysUntilOut, rawReorder };
}

/**
 * Format a single item alert line
 */
function formatItemLine(item, usage, threshold, suggestion) {
  const statusEmoji = item.quantity === 0 ? '🔴' : item.quantity <= threshold ? '🟠' : '🟡';
  let line = `${statusEmoji} <b>${item.item_name}</b> (${item.category})\n`;
  line += `   📦 Stock: <b>${item.quantity}</b> | Threshold: ${threshold}`;
  if (item.unit_price) line += ` | Price: ${Number(item.unit_price).toLocaleString()} Ks`;
  line += `\n`;
  if (usage.total_sold > 0) {
    const daily = (usage.total_sold / 7).toFixed(1);
    line += `   📊 7-day sales: ${usage.total_sold} (avg ${daily}/day)`;
    if (suggestion.daysUntilOut < 999) {
      line += ` | ⏳ Runs out in ~${suggestion.daysUntilOut} day(s)`;
    }
    line += `\n`;
    line += `   🛒 Suggested reorder: <b>${suggestion.reorderQty}</b> units`;
    if (item.unit_price) line += ` (~${suggestion.estimatedCost.toLocaleString()} Ks)`;
  }
  return line;
}

// ── Main Check (--once / default) ───────────────────────────────────────────

async function runOnceCheck() {
  log('Starting inventory check...');

  let inventory;
  try {
    inventory = await getInventory();
  } catch (e) {
    log(`MySQL connection failed: ${e.message}`);
    process.exit(1);
  }

  if (!inventory.length) {
    log('No inventory items found');
    return;
  }

  log(`Loaded ${inventory.length} inventory items`);

  const alerts = [];
  const allStatus = [];

  for (const item of inventory) {
    const threshold = getThreshold(item);
    const usage = await getItemUsage(item.item_name);
    const dailyUsage = usage.total_sold > 0 ? usage.total_sold / 7 : 0;
    const suggestion = suggestReorder(item.quantity, dailyUsage, threshold, item.unit_price);

    const isLow = item.quantity <= threshold;
    const status = {
      item: item.item_name,
      category: item.category,
      quantity: item.quantity,
      threshold,
      isLow,
      dailyUsage: dailyUsage.toFixed(1),
      daysUntilOut: suggestion.daysUntilOut,
      reorderQty: suggestion.reorderQty,
    };
    allStatus.push(status);

    if (isLow) {
      alerts.push({ item, usage, threshold, suggestion });
      log(`⚠️  LOW STOCK: ${item.item_name} — ${item.quantity} remaining (threshold: ${threshold})`);
    }
  }

  if (alerts.length === 0) {
    log('✅ All items above threshold — no alerts needed');
    return;
  }

  // Build alert message
  const now = new Date().toLocaleString('en-US', { timeZone: 'Asia/Yangon' });
  let msg = `🚨 <b>PS VIBE — LOW STOCK ALERT</b>\n`;
  msg += `📅 ${now} (MMT)\n`;
  msg += `━━━━━━━━━━━━━━━━━━━━━\n\n`;

  for (const alert of alerts) {
    msg += formatItemLine(alert.item, alert.usage, alert.threshold, alert.suggestion);
    msg += `\n`;
  }

  msg += `━━━━━━━━━━━━━━━━━━━━━\n`;
  msg += `⚠️  ${alerts.length} item(s) need restocking\n`;
  msg += `💡 <i>Reorder from supplier or adjust thresholds if stock is adequate</i>`;

  // Send alert
  await alertStaff(msg);
  log(`Alert sent for ${alerts.length} low-stock items`);
}

// ── Daily Summary ────────────────────────────────────────────────────────────

async function runDailySummary() {
  log('Generating daily inventory summary...');

  let inventory;
  try {
    inventory = await getInventory();
  } catch (e) {
    log(`MySQL connection failed: ${e.message}`);
    process.exit(1);
  }

  if (!inventory.length) {
    log('No inventory items found');
    return;
  }

  const items = [];

  for (const item of inventory) {
    const threshold = getThreshold(item);
    const usage = await getItemUsage(item.item_name);
    const dailyUsage = usage.total_sold > 0 ? usage.total_sold / 7 : 0;
    const suggestion = suggestReorder(item.quantity, dailyUsage, threshold, item.unit_price);
    const lastRestock = await getLastRestock(item.item_name);

    items.push({
      item,
      threshold,
      usage,
      dailyUsage,
      suggestion,
      lastRestock,
      isLow: item.quantity <= threshold,
    });
  }

  // Sort: low stock first, then by category
  items.sort((a, b) => {
    if (a.isLow !== b.isLow) return a.isLow ? -1 : 1;
    return a.item.category.localeCompare(b.item.category) || a.item.item_name.localeCompare(b.item.item_name);
  });

  const now = new Date().toLocaleString('en-US', { timeZone: 'Asia/Yangon' });
  let msg = `📊 <b>PS VIBE — Daily Inventory Summary</b>\n`;
  msg += `📅 ${now} (MMT)\n`;
  msg += `━━━━━━━━━━━━━━━━━━━━━\n\n`;

  // Group by category
  const categories = {};
  for (const it of items) {
    const cat = it.item.category || 'Other';
    if (!categories[cat]) categories[cat] = [];
    categories[cat].push(it);
  }

  const lowCount = items.filter(i => i.isLow).length;
  const outOfStock = items.filter(i => i.item.quantity === 0).length;

  msg += `📦 Total Items: ${items.length} | ⚠️ Low Stock: ${lowCount} | 🔴 Out: ${outOfStock}\n\n`;

  for (const [cat, catItems] of Object.entries(categories)) {
    const totalValue = catItems.reduce((sum, i) => sum + (i.item.quantity * i.item.unit_price), 0);
    msg += `<b>🏷️ ${cat}</b> (${catItems.length} items | Value: ~${totalValue.toLocaleString()} Ks)\n`;

    for (const it of catItems) {
      let emoji = '✅';
      if (it.item.quantity === 0) emoji = '🔴';
      else if (it.item.quantity <= it.threshold) emoji = '🟠';
      else if (it.item.quantity <= it.threshold * 2) emoji = '🟡';

      msg += `  ${emoji} <b>${it.item.item_name}</b>: ${it.item.quantity}`;
      if (it.dailyUsage > 0) msg += ` (${it.dailyUsage.toFixed(1)}/day, ~${it.suggestion.daysUntilOut}d left)`;
      msg += `\n`;
    }
    msg += `\n`;
  }

  // Low stock recommendations
  const lowItems = items.filter(i => i.isLow);
  if (lowItems.length > 0) {
    msg += `━━━━━━━━━━━━━━━━━━━━━\n`;
    msg += `<b>🛒 Restock Recommendations:</b>\n`;
    for (const it of lowItems) {
      msg += `  • ${it.item.item_name}: order <b>${it.suggestion.reorderQty}</b> units`;
      if (it.item.unit_price) msg += ` (~${it.suggestion.estimatedCost.toLocaleString()} Ks)`;
      msg += `\n`;
    }
  }

  msg += `\n━━━━━━━━━━━━━━━━━━━━━\n`;
  msg += `💡 <i>Automated by PS VIBE Inventory Alert System</i>`;

  await alertBoss(msg);
  log('Daily summary sent');
}

// ── Test Mode ────────────────────────────────────────────────────────────────

async function runTest() {
  log('Testing connectivity...');

  // Test MySQL
  try {
    const result = await query('SELECT COUNT(*) as count FROM inventory');
    log(`✅ MySQL OK — ${result[0].count} items in inventory`);
  } catch (e) {
    log(`❌ MySQL FAILED: ${e.message}`);
  }

  // Test Telegram
  try {
    await sendTelegram(BOSS_CHAT_ID, '🧪 <b>Inventory Alert Test</b>\n✅ System is working correctly!');
    log('✅ Telegram OK');
  } catch (e) {
    log(`❌ Telegram FAILED: ${e.message}`);
  }

  log('Test complete');
}

// ── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  if (FLAGS.test) {
    await runTest();
  } else if (FLAGS.daily) {
    await runDailySummary();
  } else {
    await runOnceCheck();
  }

  // Clean shutdown
  if (pool) await pool.end();
  process.exit(0);
}

main().catch(async (err) => {
  console.error(`[${new Date().toISOString()}] FATAL:`, err.message);
  if (pool) await pool.end().catch(() => {});
  process.exit(1);
});
