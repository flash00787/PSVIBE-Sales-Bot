# PS VIBE Social Media Auto-Reply — Infrastructure

## Overview
- **Type:** Node.js Automation
- **Runtime:** Systemd service `psvibe-social-autoreply.service`
- **Purpose:** Automated social media reply/engagement for PS VIBE
- **Framework:** Express (v5.2.1)

## Key Files
| File | Purpose |
|------|---------|
| `social_auto_reply.js` | Main automation logic |
| `knowledge/` | Knowledge base / response templates |
| `logs/` | Runtime logs |

## Features
- Automated social media reply handling
- Knowledge-based response system

## Dependencies
- Node.js
- Express v5.2.1

## Service
- Systemd unit: `psvibe-social-autoreply.service`
- Health check: `systemctl is-active psvibe-social-autoreply`
