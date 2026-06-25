# Three Brothers Construction Bot — Infrastructure

## Overview
- **Type:** Telegram Bot (Node.js)
- **Runtime:** Docker container `construction_bot`
- **Framework:** Telegraf (Node.js Telegram framework)
- **Google Sheets:** Used for COA (Chart of Accounts), Projects Master, Transactions

## Key Files
| File | Purpose |
|------|---------|
| `bot.js` | Main bot logic (Telegraf scenes) |
| `setup-sheet.js` | Google Sheet setup/initialization |
| `full-setup-sheet.js` | Complete sheet setup |
| `cash_calc.js` | Cash calculation logic |
| `setup-sheets.js` | Multi-sheet setup utility |
| `clear-data.js` | Data clearing utility |
| `Dockerfile` | Docker image definition |
| `docker-compose.yml` | Docker Compose config |
| `update.sh` | Update/deploy script |

## Features
- Chart of Accounts (COA) management
- Project tracking (Projects_Master sheet)
- Asset management (Machinery, Vehicle, Equipment, etc.)
- Transaction recording with categories
- Cash balance calculations

## Dependencies
- Node.js + Telegraf (v4.16.3)
- Google Sheets API via google-spreadsheet (v4.1.5)
- google-auth-library (v9.15.1)
- dotenv (v16.6.1)
- Docker

## Service
- Docker container: `construction_bot`
- Compose: `docker-compose.yml`
- Health check: `docker ps --filter name=construction_bot`
