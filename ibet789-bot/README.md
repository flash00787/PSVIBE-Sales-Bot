# iBet789 Telegram Bot

Control your iBet789 agent dashboard via Telegram. Built with Puppeteer for web automation.

## Features

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + instructions |
| `/login [user] [pass]` | Set agent credentials |
| `/balance` | Check agent cash balance |
| `/deposit [member_id] [amount]` | Deposit units to member |
| `/withdraw [member_id] [amount]` | Withdraw units from member |
| `/check [member_id]` | Check member info/balance |
| `/status` | Bot health & session status |
| `/help` | Show help |
| `/setup` | Setup guide |
| `/restartbrowser` | Restart browser (admin) |

## Quick Deploy

```bash
# 1. Copy files to server + run deploy script as root
bash deploy.sh

# 2. Edit credentials
nano /opt/ibet789-bot/.env

# 3. Start the bot
systemctl start ibet789-bot
systemctl status ibet789-bot

# 4. Watch logs
journalctl -u ibet789-bot -f
```

## Manual Setup

### Prerequisites
- Node.js 18+
- Debian/Ubuntu (for Chromium)

### Install
```bash
# System deps for Chromium
apt-get install -y ca-certificates fonts-liberation \
  libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 \
  libdrm2 libgbm1 libnss3 libxcomposite1 libxdamage1 \
  libxrandr2 xdg-utils unzip

# Node deps
cd /opt/ibet789-bot
npm install puppeteer node-telegram-bot-api dotenv

# Configure
cp .env.example .env
nano .env  # Fill in BOT_TOKEN, AGENT_USERNAME, AGENT_PASSWORD, ALLOWED_USERS

# Run
node bot.js
```

## Configuration (.env)

```env
BOT_TOKEN=123456:ABC-DEF1234gh...    # From @BotFather
AGENT_USERNAME=your_agent_username    # iBet789 agent login
AGENT_PASSWORD=your_password         # iBet789 agent password
AGENT_URL=https://ibet789agent.com/  # Agent dashboard URL
ALLOWED_USERS=6296803251             # Comma-separated Telegram user IDs
PUPPETEER_HEADLESS=true              # true = invisible browser
SESSION_TIMEOUT_MIN=15               # Auto re-login interval
```

## Custom Selectors

If iBet789 changes their HTML, override selectors in `.env`:

```env
SEL_USERNAME=#my-custom-username-field
SEL_BALANCE=.my-balance-class
SEL_NAV_DEPOSIT=a.nav-deposit-link
# ... see .env.example for all available selectors
```

## Security

- Bot token + agent credentials stored in `.env` (never in code)
- `ALLOWED_USERS` restricts access to specific Telegram IDs
- Session auto-expires after `SESSION_TIMEOUT_MIN` minutes
- Transaction screenshots captured for audit trail
- `/login` command persists credentials to `.env`

## File Structure

```
/opt/ibet789-bot/
├── bot.js                 # Main bot (Telegram + Puppeteer)
├── config.js              # Configuration & selectors
├── .env                   # Secrets (NOT committed to git)
├── .env.example           # Template
├── package.json           # npm config
├── node_modules/          # Dependencies
├── deploy.sh              # Deployment script
└── ibet789-bot.service    # Systemd unit file
```
