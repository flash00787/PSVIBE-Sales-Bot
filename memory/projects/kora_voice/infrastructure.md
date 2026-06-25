# Kora Voice — Infrastructure

## Project Overview
- **Type:** Node.js HTTP API (Express)
- **Owner:** Ko Aung Chan Myint
- **Slug:** `kora_voice`
- **Purpose:** Natural language command processor for staff/admin operations

## Code Paths
| Path | Purpose |
|------|---------|
| `/opt/kora-voice/` | Deployment root |
| `/opt/kora-voice/kora_voice.js` | Entry point (26KB) |
| `/opt/kora-voice/package.json` | Node.js manifest |
| `/opt/kora-voice/node_modules/` | Dependencies (77 packages) |

## API Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/command` | Parse natural language query → MySQL → formatted response |
| POST | `/tts` | Mark text as speakable for TTS |

## Services
| Service | Status | Type |
|---------|--------|------|
| `kora-voice.service` | active | systemd |

### Service Details
```
WorkingDirectory: /opt/kora-voice
ExecStart: /usr/bin/node kora_voice.js
Port: 3110
User: root
Restart: always, 5s
Environment:
  SSH_HOST="" (direct mode — no SSH tunnel)
  MYSQL_USER=psvibe_user
  MYSQL_DB=psvibe_api
  KORA_PORT=3110
  KORA_HOST=0.0.0.0
```

## Database
- **MySQL:** `psvibe_api` database on `127.0.0.1:3306`
- Connects directly (no SSH tunnel) via `DIRECT_MYSQL` mode
- User: `psvibe_user`

## Dependencies
```json
{
  "express": "^4.18.2",
  "ssh2": "^1.15.0"
}
```

## Important Notes
- SSH support is built-in but currently disabled (`SSH_HOST=""`)
- The `ssh2` dependency is included for potential remote deployment scenarios
- Can switch between direct MySQL and SSH-tunneled MySQL based on env vars

## Health Checks
```bash
systemctl is-active kora-voice
curl -s http://localhost:3110/command -X POST -H "Content-Type: application/json" -d '{"query":"status"}' | head
```

## Related Projects
- **PS VIBE:** Uses same MySQL database (`psvibe_api`)
- **Kora Host API:** Companion service
