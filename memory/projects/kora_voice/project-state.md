# Kora Voice — Current State

**Last Updated:** 2026-06-25
**Onboarded:** 2026-06-25

## Status
- **Service:** ✅ active
- **API:** Running on port 3110

## Configuration
- MySQL connected to: `psvibe_api` (direct mode)
- Port: 3110
- No SSH tunnel (running on VPS directly)

## Known Issues
- None currently identified

## Maintenance Notes
- Service depends on `docker.service` (After=network.target docker.service)
- Restart if MySQL credentials change
- Node modules should be kept updated: `cd /opt/kora-voice && npm update`

## Change Log
| Date | Change |
|------|--------|
| 2026-06-25 | Onboarded into Kora multi-project system |
