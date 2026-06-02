# 🚨 PS VIBE - Disaster Recovery Plan
**Grand Opening:** June 6, 2026
**Last Updated:** June 2, 2026

## 🏥 Service Health
| Service | Status | Uptime | Memory |
|---------|--------|--------|--------|
| psvibe-api | ✅ Running | ~2h | ~50M |
| psvibe-sale-bot | ✅ Running | ~51min | ~58M |
| psvibe-mysql | ✅ Running (Docker) | 4 days | — |

## ⚡ Quick Recovery (under 60 seconds)
- **API crash:** `systemctl restart psvibe-api`
- **Sale Bot crash:** `systemctl restart psvibe-sale-bot`
- **Customer Bot crash:** `systemctl restart psvibe_customer_bot`
- **All services:** `for s in psvibe-api psvibe-sale-bot psvibe_customer_bot; do systemctl restart $s; done`

## 📊 Check Service Status
```bash
systemctl status psvibe-api psvibe-sale-bot psvibe_customer_bot
```

## 🐬 MySQL Emergency (Docker)
- **Connection fail:** `docker restart psvibe-mysql`
- **Data loss:** Restore from `/root/backups/mysql/` (latest .gz file)
- **Full restore:**
```bash
gunzip -c /root/backups/mysql/psvibe_backup_*.sql.gz > /tmp/restore.sql
docker exec -i psvibe-mysql mysql -u root -p'PsVibe@MySQL2024!' psvibe_api < /tmp/restore.sql
rm /tmp/restore.sql
```

## 🌐 Cloudflare Tunnel
- **Website down:** `systemctl restart cloudflared-tunnel`
- **Check tunnel:** `systemctl status cloudflared-tunnel`

## 🚀 API Load Test Results (June 2, 2026)
| Endpoint | Concurrent (5x) | Avg Response | Status |
|----------|----------------|-------------|--------|
| /api/health | 200 ✅ (all 5) | ~0.016s | Healthy |
| /api/fetch_members | 401 (needs auth) | ~0.015s | Secure |
| /api/fetch_console_status | 401 (needs auth) | ~0.008s | Secure |

**Summary:** API handles concurrent requests well. Auth-protected endpoints secure.

## 🔄 Known Recovery Commands
- **Check Docker:** `docker ps --format "table {{.Names}}\t{{.Status}}"`
- **View logs:** `journalctl -u psvibe-api --tail=50`
- **Restart Docker container:** `docker restart <container-name>`

## 📞 Emergency Contact
- **Developer:** Ko Aung Chan Myint (Telegram)
