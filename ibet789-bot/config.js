/**
 * iBet789 Telegram Bot — Configuration
 */

module.exports = {
  // Agent dashboard URL (configurable per agent)
  AGENT_URL: process.env.AGENT_URL || 'https://ibet789agent.com/',

  // Telegram Bot Token from @BotFather
  BOT_TOKEN: process.env.BOT_TOKEN,

  // Agent login credentials
  AGENT_USERNAME: process.env.AGENT_USERNAME || '',
  AGENT_PASSWORD: process.env.AGENT_PASSWORD || '',

  // Comma-separated list of Telegram user IDs allowed to use the bot
  ALLOWED_USERS: (process.env.ALLOWED_USERS || '').split(',').map(Number).filter(Boolean),

  // Puppeteer options
  PUPPETEER_HEADLESS: process.env.PUPPETEER_HEADLESS !== 'false',

  // Proxy server for geo-restricted access (e.g., Myanmar proxy)
  PROXY_SERVER: process.env.PROXY_SERVER || '',

  // Session timeout in minutes (auto re-login after this)
  SESSION_TIMEOUT_MIN: parseInt(process.env.SESSION_TIMEOUT_MIN || '15', 10),

  // Navigation timeouts (ms)
  NAV_TIMEOUT: 30000,
  ELEMENT_TIMEOUT: 10000,
  ACTION_DELAY: 500, // ms between keyboard actions

  // Login page selectors (configurable per iBet789 site version)
  SELECTORS: {
    usernameField: process.env.SEL_USERNAME || '#username, input[name="username"], input[name="agent_name"], input[placeholder*="Username"], input[placeholder*="username"], input[placeholder*="Agent"]',
    passwordField: process.env.SEL_PASSWORD || '#password, input[name="password"], input[placeholder*="Password"], input[placeholder*="password"]',
    loginButton: process.env.SEL_LOGIN_BTN || 'button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Sign In"), button:has-text("LOGIN"), a:has-text("Login"), .login-btn, #login-btn',
    balanceDisplay: process.env.SEL_BALANCE || '.balance, .agent-balance, .credit, .cash, #balance, .wallet-balance, span.balance, .header-balance, [class*="balance"], [class*="Balance"], [class*="credit"]',
    memberIdField: process.env.SEL_MEMBER_ID || '#member_id, input[name="member_id"], input[name="player_id"], input[placeholder*="Member"], input[placeholder*="Player"], input[placeholder*="ID"]',
    amountField: process.env.SEL_AMOUNT || '#amount, input[name="amount"], input[name="deposit_amount"], input[name="withdraw_amount"], input[placeholder*="Amount"]',
    confirmButton: process.env.SEL_CONFIRM || 'button:has-text("Confirm"), button:has-text("Submit"), button:has-text("OK"), input[value="Confirm"], button.confirm, #confirm-btn, .btn-confirm',
    navMemberMgmt: process.env.SEL_NAV_MEMBER || 'a:has-text("Member"), a:has-text("Player"), a:has-text("Members"), a:has-text("Players"), .member-management, #member-mgmt, [class*="member"], [class*="Member"]',
    navDeposit: process.env.SEL_NAV_DEPOSIT || 'a:has-text("Deposit"), button:has-text("Deposit"), .deposit-btn, #deposit-btn, [class*="deposit"], [class*="Deposit"]',
    navWithdraw: process.env.SEL_NAV_WITHDRAW || 'a:has-text("Withdraw"), button:has-text("Withdraw"), .withdraw-btn, #withdraw-btn, [class*="withdraw"], [class*="Withdraw"], [class*="Withdrawal"]',
    successMsg: process.env.SEL_SUCCESS || '.success, .alert-success, .msg-success, [class*="success"], .green, .text-success',
    errorMsg: process.env.SEL_ERROR || '.error, .alert-error, .msg-error, [class*="error"], .red, .text-danger, .alert-danger',
    dashboardIndicator: process.env.SEL_DASHBOARD || '.dashboard, .agent-dashboard, .main-content, .main-container, #main, .header, nav.navbar, .sidebar',
  },
};
