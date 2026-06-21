# 🧠 Kora's Long-Term Memory

## People

- **Boss:** Ko Aung Chan Myint (ကိုအောင်ချမ်းမြင့်) — Founder of PS VIBE - PS5 Gaming Lounge. Call him "Boss" or "အစ်ကို" internally.
- **Osmo:** Discord username `@kingkong00787` — helped set up PS VIBE Discord server.

## Business: PS VIBE - PS5 Gaming Lounge

### Info
- **Tagline:** "Play The Game. Share The VIBE!"
- **Hours:** 9:00 AM - 9:00 PM daily
- **Address:** Yangon, Myanmar
- **Opened:** June 6, 2026 (Saturday) 🎮
- **Socials:** [Facebook](https://www.facebook.com/ps5gamecenter) | [TikTok](https://www.tiktok.com/@ps.vibe.game.cent)
- **Discord:** Guild ID 1516119712411422942 | [Invite](https://discord.gg/EXEF7phbZF)

### Infrastructure (bot-server-01: 5.223.81.16)
| Service | Purpose |
|---------|---------|
| psvibe-api | Main API server (port 8000) |
| psvibe-sale-bot | Staff sale/booking bot |
| psvibe_customer_bot | Customer-facing bot |
| psvibe-dashboard | Vue web dashboard (:9090) |
| kora-dashboard | Kora admin dashboard (:9091) |
| psvibe-discord-bot | Discord bot (35 commands) |
| MySQL | Primary database |
| cloudflared-tunnel | Cloudflare Tunnel |
| Caddy | Reverse proxy |
| n8n | Workflow automation |

### Key Operations
- **Member balance:** Column H of Card_wallet Google Sheet (legacy) → MySQL `member_wallets` (primary)
- **Receipts:** Burmese footer text must be removed
- **Coupon codes:** Valid samples: CBQVUHYG, CBANN6LD, CBZVNW7O, CBB292MP, CB7U617B

## 🧠 Critical Lessons Learned (Cumulative)

### Python Patterns
1. **`bool(0) == False`** — `"x if x else default"` breaks on 0. Use `"x if x is not None else default"`.
2. **`async def` + missing `await`** — coroutine objects silently pass type checks. Always use proper type hints.
3. **Unicode escape sequences in fix scripts** — `content.replace()` with escaped Unicode may not match file bytes. Use SFTP upload + remote execution instead.
4. **Systemd restart can silently fail** — verify PID; fallback to `kill -9` if needed.
5. **Elif chains must cover ALL variants** — `"wave"` ≠ `"wavepay"`.

### API & Database Patterns
6. **FastAPI response_model silently strips undeclared fields** — always audit response models against actual return shapes.
7. **Date format inconsistency** — Bot sends locale-dependent format (M/D/YYYY) but API expects YYYY-MM-DD. Always normalize at API boundary.
8. **API field naming is inconsistent** — camelCase (`customerName`, `timeSlot`) mixed with snake_case (`member_id`, `console_id`) in same response. Always verify field names exist before `.get()`.
9. **`today_str()` format ≠ API format** — `M/D/YYYY` vs `YYYY-MM-DD` — don't mix in comparisons.
10. **Double fail masking** — When both MySQL and GSheet fallback break simultaneously, root cause is masked. Monitor both paths independently.
11. **`%%` pattern doesn't work with `mysql.connector`** — uses `%s` parameter style, not printf. Pass format string as parameter.

### System Patterns
12. **NEVER touch ssh.socket.d** — A drop-in file created on June 11 crashed ssh.socket, taking ALL SSH down. VPS unrecoverable without Hetzner Console. Boss emphasized: "သေသေချာချာ တင်းတင်းကျပ်ကျပ် မှတ်ထားပါ".
13. **Gateway DNS failures** — Docker containers need explicit DNS config (Hetzner + Cloudflare) and `host` networking for reliable DNS.
14. **JS inline `<script>` blocks are fragile** — one syntax error kills ALL JavaScript in that block.
15. **Dashboard file deployment** — Base64 chunked SSH transfer reliable for large files. Kill stale processes before restart.
16. **`GROUP BY` collapses pipe-delimited data** — iterate all rows instead.

### Business Logic
17. **Same-console double booking** — Always check existing bookings at API level before allowing new ones.
18. **PNL depreciation must filter by purchase_date** — New assets don't accrue depreciation until month after purchase. Per agreed convention.
19. **Dashboard code is the source of truth** — Other API stubs may be outdated. Always check `dashboard_routes.py` first.
20. **FIFO for wallet consumption** — Oldest topups consumed first; bonus/free minutes have 0 Ks value.

## Major Projects & Milestones

### Grand Opening (June 6, 2026)
- Data reset: All tables cleared except 4 confirmed bookings
- 10+ critical bugs fixed in 2 days leading up (coupon, wallet, booking, sales)
- All services active and stable

### Food Cart Feature (June 14)
- Phase 1 deployed: Staff can add food to active sessions via Console → Food Sale
- Food items auto-loaded into sale voucher at session end
- Phase 2 pending: Customer Bot self-ordering

### Finance System (June 15)
- PNL & Balance Sheet endpoints fixed (were broken stubs)
- Auto-depreciation script deployed (monthly cron, 1st of month)
- Auto-amortization for prepaid rent (monthly cron)

### Discord Bot (June 15-16)
- 35 slash commands across gaming, account, community, staff modules
- Auto-mod, birthday cron, LFG system, suggestion system
- Full integration with web dashboard feedback tab

### Suggestion System (June 17)
- Full pipeline: Discord → API → Dashboard
- Staff approve/reject with embed updates

## ⚠️ Known Issues (Persistent)

| Issue | Severity | Status |
|-------|----------|--------|
| n8n payment (€25.68) overdue | Medium | Pending boss action |
| GitHub Deploy failing (psvibe-api-server) | Low | Pre-existing |
| Food Note issue — Phase 2 pending | Low | Deferred |
| VPS reboot caused DNS issues June 20 | Low | Mitigated |
| `_remind_loop` timer never fires | Low | Known, not critical |
| 100+ games claim vs 41 in DB | Low | Needs verification |

## Working Preferences

- **Language:** Burmese primary, English for tech terms
- **Timezone:** Asia/Yangon (UTC+6:30) — always convert for Boss
- **Delegation:** Always delegate complex tasks to sub-agents. Never do manually what a helper can do.
- **Fix protocol:** `python3 /root/coordination/fix_protocol.py --start <file>` before any code fix
- **Post-fix documentation:** Run `auto_doc_updater.py` + update daily memory + MEMORY.md
- **Sub-agent timeout:** 300s default
