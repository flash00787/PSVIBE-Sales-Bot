# Fix: MySQL Bound to Localhost (S-5)

**Date:** 2026-05-28 12:40 UTC  
**VPS:** 5.223.81.16  
**Status:** ✅ FIXED

## Before

```
HostIp: "" (0.0.0.0)  →  Bound to all interfaces
0.0.0.0:3306→3306/tcp, [::]:3306→3306/tcp
```

## After

```
HostIp: "127.0.0.1"   →  Bound to localhost only
127.0.0.1:3306→3306/tcp
```

## What Was Done

1. **Identified:** `psvibe-mysql` was running directly (not via docker-compose), bound to `0.0.0.0:3306`
2. **Stopped & removed:** `docker rm -f psvibe-mysql` (preserved `psvibe_mysql_data` volume)
3. **Recreated with localhost binding:**
   ```
   docker run -d --name psvibe-mysql \
     --restart unless-stopped \
     -p 127.0.0.1:3306:3306 \
     -e MYSQL_ROOT_PASSWORD='PsVibe@MySQL2024!' \
     -e MYSQL_DATABASE=psvibe_api \
     -e MYSQL_USER=psvibe_user \
     -e MYSQL_PASSWORD='PsVibe@User2024!' \
     -v psvibe_mysql_data:/var/lib/mysql \
     mysql:8.0
   ```

## Verification

- ✅ `docker ps` shows: `127.0.0.1:3306→3306/tcp`
- ✅ `ss -tlnp | grep 3306` shows: `LISTEN 127.0.0.1:3306` only
- ✅ `mysqladmin ping` returns: `mysqld is alive`
- ✅ MySQL is accessible via localhost only — no remote exposure
