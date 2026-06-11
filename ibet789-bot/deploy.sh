#!/bin/bash
# =============================================
# iBet789 Bot — Deployment Script
# Run as root on the target server
# =============================================
set -euo pipefail

echo "=== iBet789 Bot Deployment ==="
echo ""

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: This script must be run as root."
    exit 1
fi

# --- 1. Check Node.js ---
if ! command -v node &> /dev/null; then
    echo "[1/5] Node.js not found. Install Node.js 18+ first."
    echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -"
    echo "  apt-get install -y nodejs"
    exit 1
fi
echo "[1/5] Node.js: $(node -v) ✓"

# --- 2. System dependencies for Chromium ---
echo "[2/5] Installing Chromium system dependencies..."
apt-get update -qq
apt-get install -y -qq \
    ca-certificates fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libcups2 libdrm2 libgbm1 libnss3 \
    libxcomposite1 libxdamage1 libxrandr2 \
    xdg-utils unzip \
    2>/dev/null
echo "[2/5] System dependencies installed ✓"

# --- 3. Create project directory ---
echo "[3/5] Setting up project directory..."
mkdir -p /opt/ibet789-bot

# --- 4. Install npm dependencies ---
echo "[4/5] Installing npm packages..."
cd /opt/ibet789-bot
if [ ! -f package.json ]; then
    npm init -y > /dev/null 2>&1
fi
npm install puppeteer node-telegram-bot-api dotenv
echo "[4/5] npm packages installed ✓"

# --- 5. Copy files ---
echo "[5/5] Copying bot files..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/bot.js" /opt/ibet789-bot/
cp "$SCRIPT_DIR/config.js" /opt/ibet789-bot/
cp "$SCRIPT_DIR/.env.example" /opt/ibet789-bot/

# Create .env if not exists
if [ ! -f /opt/ibet789-bot/.env ]; then
    cp /opt/ibet789-bot/.env.example /opt/ibet789-bot/.env
    echo "  -> Created .env file. EDIT IT with your credentials!"
fi

# Copy and enable systemd service
cp "$SCRIPT_DIR/ibet789-bot.service" /etc/systemd/system/
systemctl daemon-reload

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit /opt/ibet789-bot/.env with your credentials"
echo "  2. Start the bot:  systemctl start ibet789-bot"
echo "  3. Check status:   systemctl status ibet789-bot"
echo "  4. View logs:      journalctl -u ibet789-bot -f"
echo ""
echo "WARNING: Do NOT start the bot until .env is configured!"
