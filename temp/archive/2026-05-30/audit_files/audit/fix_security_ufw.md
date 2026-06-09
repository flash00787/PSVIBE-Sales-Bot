# Security Fix: Block MySQL Port 3306 from Internet (S-1)

**Date:** 2026-05-28 12:39 UTC  
**VPS:** 5.223.81.16  
**Status:** ✅ FIXED

## Action Taken

Added UFW deny rules to block external access to MySQL port 3306/tcp.

### Before

No firewall rules for port 3306 existed. The port was potentially open to the internet if MySQL was listening on all interfaces.

### Commands Executed

```bash
ufw deny 3306/tcp
ufw reload
```

### After — UFW Status (numbered)

```
[ 8] 3306/tcp      DENY IN     Anywhere
[12] 3306/tcp (v6) DENY IN     Anywhere (v6)
```

Port 3306/tcp is now blocked from all incoming connections on both IPv4 and IPv6.

### Other Open Ports (for reference)

| Port   | Action   | From          |
|--------|----------|---------------|
| 22/tcp | ALLOW IN | Anywhere      |
| 80/tcp | ALLOW IN | Anywhere      |
| 443/tcp| ALLOW IN | Anywhere      |
| 8000   | ALLOW IN | Docker nets   |
| 5678   | ALLOW IN | 172.20.0.0/16 |

---

**Fix verified.** MySQL port 3306 is now firewalled from external access.
