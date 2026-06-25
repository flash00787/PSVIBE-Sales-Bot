# 📧 Email & Google

## Gmail API
- **Protocol:** OAuth 2.0 (readonly + send), token.json + secret.json
- **Sender Script:** `send_email_api.py` (urllib, HTTPS 443)
- **Sender Address:** chanmyint123456789@gmail.com
- **Refresh Token:** Auto-refresh via OAuth 2.0

## Gmail Accounts
| Account | Status | Purpose |
|---------|--------|---------|
| chanmyint123456789@gmail.com | ✅ Active | Primary |
| aungchanmyint.psvibe@gmail.com | ⏳ Pending | PS VIBE business |
| aungchanmyint.shs@gmail.com | ⏳ Pending | SHS business |

## Google Drive
- **Service Account Key:** `kora_drive_sa.json`
- **PS VIBE Drive Root:** `1V6ctTJpXaoRIDnrfxwhVO72I7jfD5GsS`

## OAuth Token Status (Updated 2026-06-25)
- **Scopes (token.json)**: drive.file only — Gmail API calls fail (scope mismatch)
- **gmail_token.json**: gmail.readonly + gmail.send — refresh token expired/revoked (HTTP 400)
- **Status**: ❌ BOTH tokens broken — needs full OAuth re-auth flow
- **Workaround**: IMAP via app password (`knpeqhkhwbvhmwey`) — WORKING ✅
  - IMAP script: `check_inbox_imap.py`
  - Send email: `send_email.py` (uses SMTP with app password, also blocked by DO)
  - Send email API may still work if token is refreshed — but needs re-auth first
- **Last Refreshed**: 2026-06-10 ~16:42 UTC
- **Drive Write**: Unknown (token expired, likely broken too)
