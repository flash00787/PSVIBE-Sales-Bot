# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Contacts

### Friends
- **You Ko Htet (ယူကိုထက်):** rein020124@gmail.com

### Colleagues / Business
- **Chan Su Su Hlaing:** chansusuhlaing@gmail.com
- **Ye Yint Oo:** yeyintoo12345678@gmail.com — Telegram ID: `8336350778`
- **Nova** — Ye Yint Oo ၏ Personal AI Assistant (OpenClaw, local setup)
- **Ye Myat (ရဲမြတ်):** yemyat.7.14.1999@gmail.com

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### API Keys

- **Grok (xAI):** `xai-yMs15u1BbMLE19zRPWQ4K4keAcqEaGVdFrVwjwL5dBCDKbM7VslrZxePhhR6evXayOdgzc1s5kFcIdKc`
  - Subagent role: Researcher (Grok 4.3)
  - New library/update research & code

- **OpenRouter:** `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`
  - Subagent role: Reviewer/Fixer (Claude Sonnet 4)
  - Code error debug when DeepSeek can't solve
  - **Model ID:** `anthropic/claude-sonnet-4` (NOT `anthropic/claude-sonnet-4-20250514` — date-specific ID expired)

### SSH

- **bot-server-01 (Main VPS):**
  - Host/IP: `5.223.81.16`
  - User: `root`
  - Private Key: `/home/node/.openclaw/workspace/.ssh/id_rsa`
  - Running Services: Caddy, n8n, agri-bot, Personal-Wallet-Tele-Bot, Sales-Tele-Bot
  - Access Info: SSH password available for `root` user with read/write and sudo privileges.
  - Connection Method: Node.js `ssh2` package (installed in workspace)
  - SSH Secret Key: `S1_PSVIBE_2024`


### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)
