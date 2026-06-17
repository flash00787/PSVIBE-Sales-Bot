# 🏗️ Infrastructure

## PS VIBE Sales Bot (V2 Modular)
- **Path:** `/root/psvibe-sales-bot/` (109 .py files)
- **GitHub:** `flash00787/PSVIBE-Sales-Bot`
- **Services:**
  - 🟢 `psvibe-sale-bot` — Main sale bot
  - 🟢 `psvibe_customer_bot` — Customer-facing bot
  - 🟢 `psvibe-api` — API server (FastAPI, port 8000)
  - 🟢 `psvibe-watchdog` — Auto-heal watchdog

## API Server (Separate Repo!)
- **Path:** `/root/psvibe_api_server/`
- **GitHub:** `flash00787/PSVIBE-API-Server`
- **CRITICAL:** Always check BOTH repos when investigating bugs!

## Architecture
```
Bot (python-telegram-bot) → API (:8000) → MySQL (primary) → gspread (cold fallback)
```
- **MySQL:** Docker container `psvibe-mysql` (127.0.0.1:3306), DB: `psvibe_api`
- **Cloudflare Tunnel:** `cloudflared-tunnel.service` — ps-vibe.com → localhost:8000
- **RECEIPT_BASE_URL:** `https://ps-vibe.com` (all encrypted)

## Coordination Tools (25+ at `/root/coordination/`)
| Tool | Lines | Purpose |
|------|-------|---------|
| Flow Analyzer | 742 | State machine, BotState mapping |
| Architecture Mapper | 754 | Module dependency graph, Mermaid/DOT |
| Enhanced Validator | 996 | Async pattern, handler validation |
| Quality Gate | 227 | Unified score 0-100 |
| Fix Protocol | 120+ | Pre/post fix safety, auto-commit |
| Workflow Engine | 330+ | 4 pipelines with auto-rollback |
| Batch Coordinator v2 | 1200 | 11 hybrid batch commands |
| Auto Healer | 190 | Service watchdog |
| Auto Doc Updater | — | Post-fix docs update (MANDATORY) |
| Tool Orchestrator | 207 | 6-tool dependency-ordered run |
| Health Monitor | — | 30 checks, 5 pillars |
| Dashboard | — | Web UI port 9090 |

## Additional Services (systemd)
| Service | Description | Status |
|---------|-------------|--------|
| `psvibe-analytics.service` | PS VIBE Predictive Analytics Engine | 🟢 Running |
| `psvibe-attendance.service` | Staff Attendance System | 🟢 Running |
| `psvibe-discord-bot.service` | Discord Bot (PS VIBE) | 🟢 Running |
| `kora-host-api.service` | Kora Host API Bridge for Nova | 🟢 Running |
| `kora-voice.service` | Kora Voice Assistant | 🟢 Running |
| `acm-personal-wallet.service` | ACM's Personal Wallet Bot | 🟢 Running |

## Shop Info
| Detail | Value |
|--------|-------|
| Name | PS VIBE - PS5 Gaming Lounge |
| Tagline | Play The Game. Share The VIBE! |
| Grand Opening | June 6, 2026 (Saturday) |
| Hours | 9 AM — 9 PM daily |
| Address | No. 17, Mau Pin Street, Sanchaung, Yangon |

## Sub-Agent Configuration
| Setting | Value |
|---------|-------|
| Default Timeout | 300s |
| System Max | 14400s (4h) |
| Max Concurrent (main) | 4 |
| Max Concurrent (subagent) | 3 |
| Max Children/Agent | 2 |
| Management Model | DeepSeek Flash |
| Code Fix Model | DeepSeek Pro |
| Fallback Chain | Pro → Flash → Gemini 2.5 Flash → Gemini 3.5 Flash |
| Auth (OpenRouter) | Claude Sonnet 4 |
| Auth (xAI) | Grok 4.3 (research) |
