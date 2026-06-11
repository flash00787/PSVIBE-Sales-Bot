/**
 * iBet789 Telegram Bot — Puppeteer Web Automation
 *
 * Controls iBet789 agent dashboard via web automation.
 * Telegram bot interface for agent operations:
 *   - Balance check
 *   - Deposit to members
 *   - Withdraw from members
 *   - Member balance inquiry
 *
 * Requirements: Node.js 18+, Puppeteer (Chromium), Telegram Bot Token
 */

'use strict';

require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');
const puppeteer = require('puppeteer');
const config = require('./config');

// ──────────────────────────────────────────────
// 0. Startup validation
// ──────────────────────────────────────────────

if (!config.BOT_TOKEN) {
  console.error('[FATAL] BOT_TOKEN is missing. Set it in .env file.');
  process.exit(1);
}

if (!config.AGENT_USERNAME || !config.AGENT_PASSWORD) {
  console.warn('[WARN] AGENT_USERNAME or AGENT_PASSWORD not set. /login command will be needed.');
}

if (config.ALLOWED_USERS.length === 0) {
  console.warn('[WARN] ALLOWED_USERS is empty. All users will be BLOCKED until configured.');
}

// ──────────────────────────────────────────────
// 1. Telegram Bot init
// ──────────────────────────────────────────────

const bot = new TelegramBot(config.BOT_TOKEN, { polling: true });

console.log('[INFO] iBet789 Telegram Bot starting...');
console.log(`[INFO] Agent URL: ${config.AGENT_URL}`);
console.log(`[INFO] Allowed users: ${config.ALLOWED_USERS.join(', ') || '(none)'}`);
console.log(`[INFO] Headless mode: ${config.PUPPETEER_HEADLESS}`);

// ──────────────────────────────────────────────
// 2. Puppeteer browser manager (singleton)
// ──────────────────────────────────────────────

let browser = null;
let page = null;
let loginTime = null;
let isBusy = false;

/**
 * Get or launch a Puppeteer browser instance.
 */
async function getBrowser() {
  if (browser && browser.isConnected()) {
    return browser;
  }

  console.log('[PUPPETEER] Launching browser...');
  browser = await puppeteer.launch({
    headless: config.PUPPETEER_HEADLESS ? 'new' : false,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--disable-web-security',
      '--disable-features=IsolateOrigins,site-per-process',
    ],
    defaultViewport: { width: 1366, height: 768 },
  });

  browser.on('disconnected', () => {
    console.log('[PUPPETEER] Browser disconnected.');
    browser = null;
    page = null;
    loginTime = null;
  });

  return browser;
}

/**
 * Close the browser and reset state.
 */
async function closeBrowser() {
  try {
    if (page) { await page.close().catch(() => {}); page = null; }
    if (browser) { await browser.close().catch(() => {}); browser = null; }
    loginTime = null;
    console.log('[PUPPETEER] Browser closed.');
  } catch (e) {
    console.error('[PUPPETEER] Error closing browser:', e.message);
  }
}

/**
 * Ensure we are logged in to the agent dashboard.
 * Returns the page object on success.
 */
async function ensureLogin() {
  const browser = await getBrowser();

  // Check if we need to re-login
  if (page && !page.isClosed() && loginTime) {
    const elapsed = (Date.now() - loginTime) / 60000; // minutes
    if (elapsed < config.SESSION_TIMEOUT_MIN) {
      return page; // session still valid
    }
    console.log(`[LOGIN] Session expired (${elapsed.toFixed(1)} min). Re-logging in...`);
    try { await page.close().catch(() => {}); } catch (_) {}
    page = null;
  }

  // Create new page
  if (!page || page.isClosed()) {
    page = await browser.newPage();
    await page.setDefaultNavigationTimeout(config.NAV_TIMEOUT);
    await page.setDefaultTimeout(config.ELEMENT_TIMEOUT);

    // Set a realistic user agent
    await page.setUserAgent(
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    );
  }

  // Perform login
  console.log(`[LOGIN] Navigating to ${config.AGENT_URL}...`);
  await page.goto(config.AGENT_URL, { waitUntil: 'networkidle2', timeout: config.NAV_TIMEOUT });

  // Small delay for any client-side redirects
  await sleep(2000);

  // Try to find login form
  const loggedIn = await isLoggedIn(page);
  if (loggedIn) {
    console.log('[LOGIN] Already logged in (session cookie).');
    loginTime = Date.now();
    return page;
  }

  // Fill username
  try {
    await page.waitForSelector(config.SELECTORS.usernameField, { timeout: 5000 });
  } catch (_) {
    // Try alternative: maybe we landed on a different page
    console.log('[LOGIN] Username field not found, checking page content...');
    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 500));
    console.log(`[LOGIN] Page snippet: ${bodyText}`);
    throw new Error('Login page not detected. Check AGENT_URL and site availability.');
  }

  console.log('[LOGIN] Filling credentials...');
  await page.type(config.SELECTORS.usernameField, config.AGENT_USERNAME, { delay: config.ACTION_DELAY });
  await page.type(config.SELECTORS.passwordField, config.AGENT_PASSWORD, { delay: config.ACTION_DELAY });

  // Click login
  await page.click(config.SELECTORS.loginButton);

  // Wait for navigation / dashboard to appear
  await sleep(3000);

  // Verify login success
  const success = await isLoggedIn(page);
  if (!success) {
    // Check for error messages
    const errorText = await getText(page, config.SELECTORS.errorMsg);
    throw new Error(errorText ? `Login failed: ${errorText}` : 'Login failed. Check credentials or site.');
  }

  loginTime = Date.now();
  console.log('[LOGIN] Login successful.');
  return page;
}

/**
 * Check if we appear to be logged in to the dashboard.
 */
async function isLoggedIn(pg) {
  try {
    const indicator = await pg.$(config.SELECTORS.dashboardIndicator);
    if (indicator) return true;

    // Also check if login fields are still visible (meaning NOT logged in)
    const loginField = await pg.$(config.SELECTORS.usernameField);
    if (loginField) return false;

    // If we can't find login form, assume logged in (dashboard may have loaded)
    return true;
  } catch (_) {
    return false;
  }
}

/**
 * Helper: get text content of first matching element.
 */
async function getText(pg, selector) {
  try {
    await pg.waitForSelector(selector, { timeout: 3000 });
    return await pg.$eval(selector, el => el.innerText.trim());
  } catch (_) {
    return null;
  }
}

/**
 * Helper: click the first matching visible element from a selector list.
 */
async function clickFirstMatch(pg, selectorList) {
  const selectors = selectorList.split(',').map(s => s.trim());
  for (const sel of selectors) {
    try {
      await pg.waitForSelector(sel, { visible: true, timeout: 3000 });
      await pg.click(sel);
      await sleep(1000);
      return sel; // return which selector matched
    } catch (_) {
      continue;
    }
  }
  throw new Error(`No element matched any of: ${selectorList}`);
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ──────────────────────────────────────────────
// 3. Agent Operations (Web Automation)
// ──────────────────────────────────────────────

/**
 * Check agent cash balance from dashboard.
 */
async function checkBalance() {
  const pg = await ensureLogin();

  // Try multiple strategies to find balance
  let balanceText = null;

  // Strategy 1: Direct selector
  balanceText = await getText(pg, config.SELECTORS.balanceDisplay);

  // Strategy 2: Look for currency patterns in page text
  if (!balanceText) {
    balanceText = await pg.evaluate(() => {
      const body = document.body.innerText;
      // Look for common balance patterns
      const patterns = [
        /Balance[:\s]*([\d,]+\.?\d*)/i,
        /Credit[:\s]*([\d,]+\.?\d*)/i,
        /Cash[:\s]*([\d,]+\.?\d*)/i,
        /Available[:\s]*([\d,]+\.?\d*)/i,
        /(?:฿|THB|MMK|USD|EUR)\s*([\d,]+\.?\d*)/,
        /([\d,]+\.?\d*)\s*(?:฿|THB|MMK|บาท)/,
      ];
      for (const pattern of patterns) {
        const match = body.match(pattern);
        if (match) return match[1] || match[0];
      }
      return null;
    });
  }

  if (!balanceText) {
    return { success: false, error: 'Could not locate balance on dashboard. The page layout may have changed.' };
  }

  return { success: true, balance: balanceText.trim() };
}

/**
 * Deposit units to a member account.
 */
async function depositToMember(memberId, amount) {
  const pg = await ensureLogin();
  amount = parseFloat(amount);

  if (isNaN(amount) || amount <= 0) {
    return { success: false, error: 'Invalid amount. Must be a positive number.' };
  }

  // Navigate to deposit page
  await navigateTo(pg, 'deposit');

  // Enter member ID
  await pg.waitForSelector(config.SELECTORS.memberIdField, { visible: true, timeout: 5000 });
  await pg.click(config.SELECTORS.memberIdField, { clickCount: 3 }); // select all
  await pg.type(config.SELECTORS.memberIdField, memberId, { delay: config.ACTION_DELAY });

  // Enter amount
  await pg.waitForSelector(config.SELECTORS.amountField, { visible: true, timeout: 3000 });
  await pg.click(config.SELECTORS.amountField, { clickCount: 3 });
  await pg.type(config.SELECTORS.amountField, String(amount), { delay: config.ACTION_DELAY });

  await sleep(500);

  // Take screenshot before confirming (for audit)
  const screenshotBuf = await pg.screenshot({ encoding: 'base64', fullPage: false });

  // Click confirm
  await clickFirstMatch(pg, config.SELECTORS.confirmButton);

  // Wait for result
  await sleep(3000);

  // Check for success/error
  const successMsg = await getText(pg, config.SELECTORS.successMsg);
  const errorMsg = await getText(pg, config.SELECTORS.errorMsg);

  if (successMsg && !errorMsg) {
    return { success: true, message: successMsg, amount, memberId, screenshot: screenshotBuf };
  } else if (errorMsg) {
    return { success: false, error: errorMsg, screenshot: screenshotBuf };
  }

  // If ambiguous, take a broader look
  const pageText = await pg.evaluate(() => document.body.innerText.substring(0, 1000));
  return {
    success: !pageText.toLowerCase().includes('error') && !pageText.toLowerCase().includes('fail'),
    message: 'Transaction processed. Check the confirmation on dashboard.',
    amount,
    memberId,
    screenshot: screenshotBuf,
  };
}

/**
 * Withdraw units from a member account.
 */
async function withdrawFromMember(memberId, amount) {
  const pg = await ensureLogin();
  amount = parseFloat(amount);

  if (isNaN(amount) || amount <= 0) {
    return { success: false, error: 'Invalid amount. Must be a positive number.' };
  }

  // Navigate to withdraw page
  await navigateTo(pg, 'withdraw');

  // Enter member ID
  await pg.waitForSelector(config.SELECTORS.memberIdField, { visible: true, timeout: 5000 });
  await pg.click(config.SELECTORS.memberIdField, { clickCount: 3 });
  await pg.type(config.SELECTORS.memberIdField, memberId, { delay: config.ACTION_DELAY });

  // Enter amount
  await pg.waitForSelector(config.SELECTORS.amountField, { visible: true, timeout: 3000 });
  await pg.click(config.SELECTORS.amountField, { clickCount: 3 });
  await pg.type(config.SELECTORS.amountField, String(amount), { delay: config.ACTION_DELAY });

  await sleep(500);

  const screenshotBuf = await pg.screenshot({ encoding: 'base64', fullPage: false });

  // Click confirm
  await clickFirstMatch(pg, config.SELECTORS.confirmButton);

  await sleep(3000);

  const successMsg = await getText(pg, config.SELECTORS.successMsg);
  const errorMsg = await getText(pg, config.SELECTORS.errorMsg);

  if (successMsg && !errorMsg) {
    return { success: true, message: successMsg, amount, memberId, screenshot: screenshotBuf };
  } else if (errorMsg) {
    return { success: false, error: errorMsg, screenshot: screenshotBuf };
  }

  const pageText = await pg.evaluate(() => document.body.innerText.substring(0, 1000));
  return {
    success: !pageText.toLowerCase().includes('error') && !pageText.toLowerCase().includes('fail'),
    message: 'Transaction processed. Check the confirmation on dashboard.',
    amount,
    memberId,
    screenshot: screenshotBuf,
  };
}

/**
 * Check member info/balance.
 */
async function checkMember(memberId) {
  const pg = await ensureLogin();

  // Navigate to member management section
  await navigateTo(pg, 'member');

  // Search for the member
  await pg.waitForSelector(config.SELECTORS.memberIdField, { visible: true, timeout: 5000 });
  await pg.click(config.SELECTORS.memberIdField, { clickCount: 3 });
  await pg.type(config.SELECTORS.memberIdField, memberId, { delay: config.ACTION_DELAY });

  // Try to find and click a search/submit button
  try {
    await clickFirstMatch(pg, config.SELECTORS.confirmButton);
  } catch (_) {
    // Maybe pressing Enter works
    await pg.keyboard.press('Enter');
  }

  await sleep(3000);

  // Capture the result area
  const screenshotBuf = await pg.screenshot({ encoding: 'base64', fullPage: false });

  // Try to extract relevant info
  const info = await pg.evaluate(() => {
    const body = document.body.innerText;
    // Get a chunk of the page that might contain member info
    const lines = body.split('\n').filter(l => l.trim().length > 0);
    // Try to find relevant section
    let relevantLines = [];
    let capturing = false;
    for (const line of lines) {
      if (/member|player|balance|credit|name|id|status/i.test(line)) {
        capturing = true;
      }
      if (capturing) {
        relevantLines.push(line.trim());
        if (relevantLines.length > 20) break;
      }
    }
    if (relevantLines.length === 0) {
      relevantLines = lines.slice(0, 30); // fallback: first 30 lines
    }
    return relevantLines.join('\n').substring(0, 1500);
  });

  return {
    success: true,
    memberId,
    info,
    screenshot: screenshotBuf,
  };
}

/**
 * Navigate to a specific section of the dashboard.
 */
async function navigateTo(pg, section) {
  switch (section) {
    case 'deposit':
      try {
        await clickFirstMatch(pg, config.SELECTORS.navDeposit);
      } catch (e) {
        // Fallback: try navigating through member management first
        try { await clickFirstMatch(pg, config.SELECTORS.navMemberMgmt); await sleep(1000); } catch (_) {}
        await clickFirstMatch(pg, config.SELECTORS.navDeposit);
      }
      break;

    case 'withdraw':
      try {
        await clickFirstMatch(pg, config.SELECTORS.navWithdraw);
      } catch (e) {
        try { await clickFirstMatch(pg, config.SELECTORS.navMemberMgmt); await sleep(1000); } catch (_) {}
        await clickFirstMatch(pg, config.SELECTORS.navWithdraw);
      }
      break;

    case 'member':
      await clickFirstMatch(pg, config.SELECTORS.navMemberMgmt);
      break;
  }

  await sleep(1000);
}

// ──────────────────────────────────────────────
// 4. Authentication Middleware
// ──────────────────────────────────────────────

function authMiddleware(msg) {
  const userId = msg.from?.id;
  if (!userId) return false;
  if (config.ALLOWED_USERS.length === 0) return false; // block all if not configured
  return config.ALLOWED_USERS.includes(userId);
}

function getUserId(msg) {
  return msg.from?.id || 'unknown';
}

// ──────────────────────────────────────────────
// 5. Command Handlers
// ──────────────────────────────────────────────

bot.onText(/\/start/, async (msg) => {
  const userId = getUserId(msg);
  console.log(`[CMD] /start from ${userId}`);

  const welcomeMsg =
    `🤖 *iBet789 Agent Bot*\n\n` +
    `Control your iBet789 agent account via Telegram.\n\n` +
    `*Commands:*\n` +
    `🔐 /login \\[username\\] \\[password\\] — Set agent credentials\n` +
    `💰 /balance — Check agent cash balance\n` +
    `📥 /deposit \\[member_id\\] \\[amount\\] — Deposit units\n` +
    `📤 /withdraw \\[member_id\\] \\[amount\\] — Withdraw units\n` +
    `🔍 /check \\[member_id\\] — Check member info\n` +
    `🔧 /status — Bot & session status\n` +
    `❓ /help — Show this help\n\n` +
    `⚠️ *Security:* Only authorized users can execute commands.`;

  bot.sendMessage(msg.chat.id, welcomeMsg, { parse_mode: 'Markdown' });
});

bot.onText(/\/help/, async (msg) => {
  const userId = getUserId(msg);
  console.log(`[CMD] /help from ${userId}`);

  const helpMsg =
    `📋 *iBet789 Bot Help*\n\n` +
    `*Authentication*\n` +
    `Set your agent credentials first:\n` +
    `\`/login your_agent_username your_password\`\n\n` +
    `*Operations*\n` +
    `• \`/balance\` — Shows current agent wallet balance\n` +
    `• \`/deposit MEMBER123 500\` — Deposits 500 units to MEMBER123\n` +
    `• \`/withdraw MEMBER123 200\` — Withdraws 200 units from MEMBER123\n` +
    `• \`/check MEMBER123\` — Shows member balance & info\n` +
    `• \`/status\` — Bot health & login status\n\n` +
    `*Setup*\n` +
    `• Configure \`AGENT_URL\` in .env for your agent domain\n` +
    `• Set \`ALLOWED_USERS\` to your Telegram user ID\n` +
    `• Selectors can be customized via env vars (see config.js)\n\n` +
    `⚙️ Admin: /setup — Setup guide`;

  bot.sendMessage(msg.chat.id, helpMsg, { parse_mode: 'Markdown' });
});

bot.onText(/\/setup/, async (msg) => {
  const userId = getUserId(msg);
  if (!authMiddleware(msg)) {
    return bot.sendMessage(msg.chat.id, '⛔ Unauthorized.');
  }

  const setupMsg =
    `⚙️ *Setup Guide*\n\n` +
    `1️⃣ Create \`.env\` file:\n` +
    `\`\`\`\nBOT_TOKEN=your_telegram_bot_token\nAGENT_USERNAME=your_agent_username\nAGENT_PASSWORD=your_agent_password\nAGENT_URL=https://ibet789agent.com/\nALLOWED_USERS=${userId}\n\`\`\`\n\n` +
    `2️⃣ Install system deps:\n` +
    `\`\`\`bash\napt-get install -y ca-certificates fonts-liberation \\\n  libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 \\\n  libdrm2 libgbm1 libnss3 libxcomposite1 \\\n  libxdamage1 libxrandr2 xdg-utils unzip\n\`\`\`\n\n` +
    `3️⃣ Start the bot:\n` +
    `\`\`\`bash\ncd /opt/ibet789-bot\nnode bot.js\n\`\`\`\n\n` +
    `Or use systemd:\n` +
    `\`\`\`bash\nsystemctl enable --now ibet789-bot\n\`\`\``;

  bot.sendMessage(msg.chat.id, setupMsg, { parse_mode: 'Markdown' });
});

bot.onText(/\/login(?:\s+(\S+)\s+(.+))?/, async (msg, match) => {
  const userId = getUserId(msg);
  if (!authMiddleware(msg)) {
    return bot.sendMessage(msg.chat.id, '⛔ Unauthorized.');
  }

  if (!match[1] || !match[2]) {
    return bot.sendMessage(
      msg.chat.id,
      '❌ Usage: `/login [username] [password]`\nExample: `/login agent123 mypassword`',
      { parse_mode: 'Markdown' }
    );
  }

  const username = match[1].trim();
  const password = match[2].trim();

  // Update in-memory config (live session)
  config.AGENT_USERNAME = username;
  config.AGENT_PASSWORD = password;

  // Also update .env file for persistence
  try {
    const fs = require('fs');
    const path = require('path');
    const envPath = path.join(__dirname, '.env');
    let envContent = '';
    try {
      envContent = fs.readFileSync(envPath, 'utf8');
    } catch (_) {}

    // Update or add lines
    const lines = envContent.split('\n');
    let updatedUsername = false, updatedPassword = false;
    const newLines = lines.map(line => {
      if (line.startsWith('AGENT_USERNAME=')) { updatedUsername = true; return `AGENT_USERNAME=${username}`; }
      if (line.startsWith('AGENT_PASSWORD=')) { updatedPassword = true; return `AGENT_PASSWORD=${password}`; }
      return line;
    }).filter(l => l.trim() !== '');

    if (!updatedUsername) newLines.push(`AGENT_USERNAME=${username}`);
    if (!updatedPassword) newLines.push(`AGENT_PASSWORD=${password}`);

    fs.writeFileSync(envPath, newLines.join('\n') + '\n');
  } catch (e) {
    console.error('[ENV] Failed to persist credentials:', e.message);
  }

  // Force re-login on next operation
  loginTime = null;

  bot.sendMessage(msg.chat.id, '✅ Credentials saved. They will be used for the next operation.\nTry `/balance` to verify login works.');
});

bot.onText(/\/balance/, async (msg) => {
  const userId = getUserId(msg);
  if (!authMiddleware(msg)) {
    return bot.sendMessage(msg.chat.id, '⛔ Unauthorized.');
  }

  if (isBusy) {
    return bot.sendMessage(msg.chat.id, '⏳ Bot is processing another request. Please wait.');
  }

  if (!config.AGENT_USERNAME || !config.AGENT_PASSWORD) {
    return bot.sendMessage(msg.chat.id, '⚠️ No credentials set. Use `/login [username] [password]` first.');
  }

  const statusMsg = await bot.sendMessage(msg.chat.id, '💰 Checking balance...');

  try {
    isBusy = true;
    const result = await checkBalance();

    if (result.success) {
      await bot.editMessageText(`💰 *Agent Balance:* \`${result.balance}\``, {
        chat_id: msg.chat.id,
        message_id: statusMsg.message_id,
        parse_mode: 'Markdown',
      });
    } else {
      await bot.editMessageText(`❌ Failed to get balance: ${result.error}`, {
        chat_id: msg.chat.id,
        message_id: statusMsg.message_id,
      });
    }
  } catch (error) {
    console.error('[BALANCE] Error:', error.message);
    await bot.editMessageText(`❌ Error: ${error.message}`, {
      chat_id: msg.chat.id,
      message_id: statusMsg.message_id,
    });
  } finally {
    isBusy = false;
  }
});

bot.onText(/\/deposit(?:\s+(\S+)\s+(\d+\.?\d*))?/, async (msg, match) => {
  const userId = getUserId(msg);
  if (!authMiddleware(msg)) {
    return bot.sendMessage(msg.chat.id, '⛔ Unauthorized.');
  }

  if (isBusy) {
    return bot.sendMessage(msg.chat.id, '⏳ Bot is processing another request. Please wait.');
  }

  if (!config.AGENT_USERNAME || !config.AGENT_PASSWORD) {
    return bot.sendMessage(msg.chat.id, '⚠️ No credentials set. Use `/login [username] [password]` first.');
  }

  if (!match[1] || !match[2]) {
    return bot.sendMessage(
      msg.chat.id,
      '❌ Usage: `/deposit [member_id] [amount]`\nExample: `/deposit MEMBER001 500`',
      { parse_mode: 'Markdown' }
    );
  }

  const memberId = match[1].trim();
  const amount = match[2].trim();

  const statusMsg = await bot.sendMessage(msg.chat.id, `📥 Depositing ${amount} to \`${memberId}\`...`, { parse_mode: 'Markdown' });

  try {
    isBusy = true;
    const result = await depositToMember(memberId, amount);

    if (result.success) {
      let response = `✅ *Deposit Successful*\n\nMember: \`${memberId}\`\nAmount: \`${amount}\`\n${result.message ? `\n${result.message}` : ''}`;
      await bot.editMessageText(response, {
        chat_id: msg.chat.id,
        message_id: statusMsg.message_id,
        parse_mode: 'Markdown',
      });

      // Send screenshot as document if available
      if (result.screenshot) {
        try {
          await bot.sendPhoto(msg.chat.id, Buffer.from(result.screenshot, 'base64'), {
            caption: `🧾 Deposit receipt: ${memberId}`,
          });
        } catch (_) {
          // Screenshot might be too large or other issue
        }
      }
    } else {
      await bot.editMessageText(`❌ *Deposit Failed*\n\nMember: \`${memberId}\`\nError: ${result.error}`, {
        chat_id: msg.chat.id,
        message_id: statusMsg.message_id,
        parse_mode: 'Markdown',
      });
    }
  } catch (error) {
    console.error('[DEPOSIT] Error:', error.message);
    await bot.editMessageText(`❌ Error: ${error.message}`, {
      chat_id: msg.chat.id,
      message_id: statusMsg.message_id,
    });
  } finally {
    isBusy = false;
  }
});

bot.onText(/\/withdraw(?:\s+(\S+)\s+(\d+\.?\d*))?/, async (msg, match) => {
  const userId = getUserId(msg);
  if (!authMiddleware(msg)) {
    return bot.sendMessage(msg.chat.id, '⛔ Unauthorized.');
  }

  if (isBusy) {
    return bot.sendMessage(msg.chat.id, '⏳ Bot is processing another request. Please wait.');
  }

  if (!config.AGENT_USERNAME || !config.AGENT_PASSWORD) {
    return bot.sendMessage(msg.chat.id, '⚠️ No credentials set. Use `/login [username] [password]` first.');
  }

  if (!match[1] || !match[2]) {
    return bot.sendMessage(
      msg.chat.id,
      '❌ Usage: `/withdraw [member_id] [amount]`\nExample: `/withdraw MEMBER001 200`',
      { parse_mode: 'Markdown' }
    );
  }

  const memberId = match[1].trim();
  const amount = match[2].trim();

  const statusMsg = await bot.sendMessage(msg.chat.id, `📤 Withdrawing ${amount} from \`${memberId}\`...`, { parse_mode: 'Markdown' });

  try {
    isBusy = true;
    const result = await withdrawFromMember(memberId, amount);

    if (result.success) {
      let response = `✅ *Withdrawal Successful*\n\nMember: \`${memberId}\`\nAmount: \`${amount}\`\n${result.message ? `\n${result.message}` : ''}`;
      await bot.editMessageText(response, {
        chat_id: msg.chat.id,
        message_id: statusMsg.message_id,
        parse_mode: 'Markdown',
      });

      if (result.screenshot) {
        try {
          await bot.sendPhoto(msg.chat.id, Buffer.from(result.screenshot, 'base64'), {
            caption: `🧾 Withdrawal receipt: ${memberId}`,
          });
        } catch (_) {}
      }
    } else {
      await bot.editMessageText(`❌ *Withdrawal Failed*\n\nMember: \`${memberId}\`\nError: ${result.error}`, {
        chat_id: msg.chat.id,
        message_id: statusMsg.message_id,
        parse_mode: 'Markdown',
      });
    }
  } catch (error) {
    console.error('[WITHDRAW] Error:', error.message);
    await bot.editMessageText(`❌ Error: ${error.message}`, {
      chat_id: msg.chat.id,
      message_id: statusMsg.message_id,
    });
  } finally {
    isBusy = false;
  }
});

bot.onText(/\/check(?:\s+(\S+))?/, async (msg, match) => {
  const userId = getUserId(msg);
  if (!authMiddleware(msg)) {
    return bot.sendMessage(msg.chat.id, '⛔ Unauthorized.');
  }

  if (isBusy) {
    return bot.sendMessage(msg.chat.id, '⏳ Bot is processing another request. Please wait.');
  }

  if (!config.AGENT_USERNAME || !config.AGENT_PASSWORD) {
    return bot.sendMessage(msg.chat.id, '⚠️ No credentials set. Use `/login [username] [password]` first.');
  }

  if (!match[1]) {
    return bot.sendMessage(
      msg.chat.id,
      '❌ Usage: `/check [member_id]`\nExample: `/check MEMBER001`',
      { parse_mode: 'Markdown' }
    );
  }

  const memberId = match[1].trim();
  const statusMsg = await bot.sendMessage(msg.chat.id, `🔍 Checking member \`${memberId}\`...`, { parse_mode: 'Markdown' });

  try {
    isBusy = true;
    const result = await checkMember(memberId);

    if (result.success) {
      const infoPreview = result.info.length > 500
        ? result.info.substring(0, 500) + '...'
        : result.info;

      await bot.editMessageText(
        `🔍 *Member Info: ${memberId}*\n\n\`\`\`\n${infoPreview}\n\`\`\``,
        {
          chat_id: msg.chat.id,
          message_id: statusMsg.message_id,
          parse_mode: 'Markdown',
        }
      );

      if (result.screenshot) {
        try {
          await bot.sendPhoto(msg.chat.id, Buffer.from(result.screenshot, 'base64'), {
            caption: `📸 Screenshot: ${memberId}`,
          });
        } catch (_) {}
      }
    } else {
      await bot.editMessageText(`❌ Failed to check member: ${result.error}`, {
        chat_id: msg.chat.id,
        message_id: statusMsg.message_id,
      });
    }
  } catch (error) {
    console.error('[CHECK] Error:', error.message);
    await bot.editMessageText(`❌ Error: ${error.message}`, {
      chat_id: msg.chat.id,
      message_id: statusMsg.message_id,
    });
  } finally {
    isBusy = false;
  }
});

bot.onText(/\/status/, async (msg) => {
  const userId = getUserId(msg);
  if (!authMiddleware(msg)) {
    return bot.sendMessage(msg.chat.id, '⛔ Unauthorized.');
  }

  const browserRunning = browser && browser.isConnected();
  const sessionAge = loginTime ? `${((Date.now() - loginTime) / 60000).toFixed(1)} min` : 'none';
  const credsSet = !!(config.AGENT_USERNAME && config.AGENT_PASSWORD);

  const statusMsg =
    `🔧 *Bot Status*\n\n` +
    `🌐 Agent URL: \`${config.AGENT_URL}\`\n` +
    `🔐 Credentials: ${credsSet ? '✅ Set' : '❌ Not set'}\n` +
    `🌍 Browser: ${browserRunning ? '✅ Running' : '❌ Not running'}\n` +
    `⏱️ Session Age: ${sessionAge}\n` +
    `⏰ Session Timeout: ${config.SESSION_TIMEOUT_MIN} min\n` +
    `📋 Busy: ${isBusy ? 'Yes' : 'No'}\n` +
    `👤 Allowed Users: ${config.ALLOWED_USERS.join(', ') || '(none)'}`;

  bot.sendMessage(msg.chat.id, statusMsg, { parse_mode: 'Markdown' });
});

bot.onText(/\/restartbrowser/, async (msg) => {
  const userId = getUserId(msg);
  if (!authMiddleware(msg)) {
    return bot.sendMessage(msg.chat.id, '⛔ Unauthorized.');
  }

  await bot.sendMessage(msg.chat.id, '🔄 Restarting browser...');
  await closeBrowser();
  await bot.sendMessage(msg.chat.id, '✅ Browser restarted. Next command will re-login.');
});

// Handle unexpected errors
bot.on('polling_error', (error) => {
  console.error('[POLLING ERROR]', error.message);
});

bot.on('error', (error) => {
  console.error('[BOT ERROR]', error.message);
});

// ──────────────────────────────────────────────
// 6. Graceful shutdown
// ──────────────────────────────────────────────

async function shutdown(signal) {
  console.log(`[SHUTDOWN] Received ${signal}. Cleaning up...`);
  try {
    bot.stopPolling();
  } catch (_) {}
  await closeBrowser();
  console.log('[SHUTDOWN] Done. Goodbye.');
  process.exit(0);
}

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('unhandledRejection', (reason) => {
  console.error('[UNHANDLED REJECTION]', reason);
});
process.on('uncaughtException', (error) => {
  console.error('[UNCAUGHT EXCEPTION]', error.message);
  // Don't exit — keep the bot running
});

console.log('[INFO] Bot is ready. Waiting for commands...');
