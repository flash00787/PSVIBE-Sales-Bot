# Security Hardening Report — VPS 5.223.81.16
**Date:** 2026-06-13 07:05–07:09 UTC  
**Performed by:** OpenClaw Subagent via Node.js SSH2  
**Status:** ✅ Complete

---

## Task 1: SSH Key Audit & Security ✅

### Before
- `PermitRootLogin yes` (allowed root password login)
- `PasswordAuthentication` not explicitly set (defaulted to yes)

### After
```
PermitRootLogin prohibit-password
PasswordAuthentication no
PubkeyAuthentication yes  (default)
Port 22, 80, 443, 22222   (unchanged)
```

### Actions
- Changed `PermitRootLogin` from `yes` → `prohibit-password`
- Added explicit `PasswordAuthentication no`
- Ran `sshd -t` — passed clean
- Restarted sshd successfully
- Connection verified working after restart

### Authorized Keys
- 10 entries in `/root/.ssh/authorized_keys`
- Primary keys: DigitalOcean DOTTY key + ubuntu key
- Keys intact, not modified

---

## Task 2: fail2ban Audit & Tuning ✅

### Before
- fail2ban was **not installed** — zero brute-force protection

### After
- Installed `fail2ban` via apt
- Created `/etc/fail2ban/jail.local`:
  ```ini
  [sshd]
  enabled = true
  bantime = 3600
  maxretry = 5
  findtime = 600
  ```
- Enabled & started systemd service
- **5 IPs already banned at time of activation:**
  - `177.30.64.65`, `185.227.153.56`, `213.209.159.56`, `45.148.10.141`, `80.94.92.184`
- SSH jail active and filtering

### Status
```
Status for the jail: sshd
|- Filter
|  |- Currently failed: 2
|  |- Total failed:     4
|- Actions
   |- Currently banned: 5
   |- Total banned:     5
```

---

## Task 3: System Auto-Backup Setup ✅

### Backup Script: `/root/auto_backup.sh`
- **MySQL dump:** `docker exec psvibe-mysql mysqldump ...` → dumps `psvibe_api` database
- **File backups:** Tars `/root/psvibe-sales-bot/` and `/root/psvibe_api_server/`
- **Compression:** SQL dumps gzipped immediately
- **Retention:** 7-day cleanup of `.sql.gz` and `.tar.gz` files
- **Logging:** `/var/log/auto_backup.log`

### MySQL Credentials
- Created `/root/.my.cnf` (mode 600) with database credentials
- Database: `psvibe_api` (not `psvibe_sales` — corrected)
- MySQL running in Docker container `psvibe-mysql`

### Cron
```
0 2 * * * /bin/bash /root/auto_backup.sh   ← NEW: Daily 2AM UTC backup
```
Existing cron jobs (EOD report, booking reminder, auto-cancel) preserved.

### Test Results
| File | Size | Status |
|------|------|--------|
| `psvibe_api_20260613_070824.sql.gz` | 38 KB | ✅ |
| `psvibe_sales_bot_20260613_070824.tar.gz` | 33 MB | ✅ |
| `psvibe_api_server_20260613_070824.tar.gz` | 85 MB | ✅ |

---

## Task 4: Firewall Check ✅

### UFW Status: ACTIVE
```
Default: deny (incoming), allow (outgoing), deny (routed)

22/tcp    ALLOW IN   Anywhere      ← SSH
80/tcp    ALLOW IN   Anywhere      ← HTTP
443/tcp   ALLOW IN   Anywhere      ← HTTPS
8000      ALLOW IN   172.17-20.0.0/16  ← Docker internal
5678      ALLOW IN   172.20.0.0/16     ← n8n
9091/tcp  ALLOW IN   172.16.0.0/12     ← Kora Dashboard
3306/tcp  DENY IN    Anywhere      ← MySQL (BLOCKED externally!) ✅
```

### Findings
- **MySQL port 3306 is DENIED externally** — excellent
- Docker bridge networks have internal access on port 8000
- Kora Dashboard (9091) restricted to private network range
- IPv6 rules mirror IPv4 — consistent
- UFW was already enabled and well-configured — no changes needed

---

## Task 5: Docker Container Security ✅

### Running Containers
| Container | Image | User | Ports |
|-----------|-------|------|-------|
| `oc-nova` | openclaw:latest | `node` | 3002→3000 |
| `oc-coco` | openclaw:latest | `node` | 3003→3000 |
| `gateway` | openclaw:local | `node` | 18789-18790 |
| `construction_bot` | construction-bot-bot | `bot` | — |
| `n8n` | n8nio/n8n:latest | `node` | 5678 (loopback) |
| `psvibe-mysql` | mysql:8.0 | **root** ⚠️ | 3306 (loopback) |
| `caddy-1` | caddy:latest | **root** ⚠️ | — |

### Security Notes
- ✅ 5/7 containers run as non-root (`node`, `bot`)
- ⚠️ `psvibe-mysql` runs as root — **standard for MySQL official Docker image**; acceptable as it binds only to loopback
- ⚠️ `aungchanmyint-caddy-1` runs as root — **standard for Caddy** (needs port 80/443); acceptable
- Docker daemon logging: `json-file, max-size=10m, max-file=3` — good for log rotation
- MySQL container environment contains plaintext passwords — this is standard Docker practice but consider using Docker secrets in production

---

## Summary

| Task | Status | Changes |
|------|--------|---------|
| SSH Hardening | ✅ Complete | `PermitRootLogin prohibit-password`, `PasswordAuthentication no` |
| fail2ban | ✅ Installed | Installed, configured, 5 IPs already banned |
| Auto-Backup | ✅ Installed | Daily 2AM UTC, MySQL + app directories, 7-day retention |
| Firewall | ✅ Verified | Already active and well-configured (no changes needed) |
| Docker Audit | ✅ Complete | 5/7 non-root, documented exceptions |

## Recommendations (Not Implemented — For Review)
1. **Consider reducing SSH ports** — SSH is exposed on 22, 80, 443, 22222 (this is deliberate for bypassing firewalls but increases attack surface)
2. **MySQL `.my.cnf`** created with credentials — ensure it's backed up and secured
3. **Backup rotation** — 7-day retention confirmed; consider off-server backups (S3, Google Drive)
4. **Docker secrets** — MySQL passwords are in container environment variables; consider secrets manager
5. **Regular audit** — Re-run this audit weekly via cron
