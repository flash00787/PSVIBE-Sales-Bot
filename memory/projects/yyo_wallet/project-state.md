# YYO Wallet — Current State

**Last Updated:** 2026-06-25
**Onboarded:** 2026-06-25

## Status
- **Service:** ✅ active
- **Bot:** Running normally

## Configuration
- Bot token in: `bot/.env`
- Google Service Account: `bot/service_account.json`
- Google Sheet: Transaction_Log worksheet
- Workspace configured for personal finance tracking

## Known Issues
- None currently identified

## Maintenance Notes
- Log files in `bot/` can grow large — rotate regularly
- Bot uses ConversationHandler with PicklePersistence — state file is `bot/conversation_state.pkl`
- If Google Sheets API quota exceeded, bot will fail gracefully

## Change Log
| Date | Change |
|------|--------|
| 2026-06-25 | Onboarded into Kora multi-project system |
