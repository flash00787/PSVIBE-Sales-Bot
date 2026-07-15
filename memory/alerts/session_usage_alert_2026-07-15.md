# Session Usage Alert

**Date:** 2026-07-15 09:19 UTC
**Status:** 🔴 SESSION_WARN — Above threshold

| Metric | Value |
|--------|-------|
| Usage | **84%** |
| Used | 420 MB |
| Limit | 500 MB |
| Threshold | 80% |

**Recommended Actions:**
1. Run `bash /root/.openclaw/workspace/memory/scripts/bulk_session_cleanup.sh` to prune old sessions
2. Or increase `session.maintenance.maxDiskBytes` in gateway config
3. Or archive/rotate sessions manually via `smart_session_cleanup.sh`

**Script result:**
```
⚠️ SESSION_WARN: 84% used (420MB/500MB)
ACTION: Clean old sessions or increase session.maintenance.maxDiskBytes
```
