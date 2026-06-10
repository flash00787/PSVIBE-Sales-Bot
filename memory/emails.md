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

## OAuth Token Status (Updated 2026-06-10)
- **Scopes**: gmail.readonly + gmail.send + drive.file ✅
- **Refresh Token**: Active — auto-refreshes access_token on expiry
- **Last Refreshed**: 2026-06-10 ~16:42 UTC
- **Drive Write**: ✅ Working (PS VIBE folder — direct upload via OAuth token)
