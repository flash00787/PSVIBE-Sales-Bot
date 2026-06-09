FIX-09 | Broadcast Validation | DONE | broadcast.py | 

Changes applied to `/root/psvibe-sale-bot/bot/handlers/broadcast.py` on `5.223.81.16`:

1. **Import `html` + `asyncio`** (line 6): `import logging, re, json, html, asyncio`
   - Note: `asyncio` was previously used but never imported — this was a latent bug.

2. **HTML escaping + 1000-char cap** (line 55): `safe_text = html.escape(msg_text)[:1000]`
   - Prevents HTML injection in broadcast messages
   - Caps message length to prevent abuse

3. **Opt-out footer** (line 56): `full_text = f"...\n\n—\n<i>Unsubscribe /stop</i>"`
   - Every broadcast now includes an unsubscribe prompt

4. **Rate limiting** (line 68): `asyncio.sleep(0.1)` changed from `0.05`
   - Now ~10 msg/s, well under the 30 msg/s Telegram limit

5. **Completion logging** (line 73): `logging.info("Broadcast complete: sent=%d, failed=%d, total_targets=%d", ...)`
   - Total recipients and failures logged

All edits verified on the remote server via grep line-number confirmation.
