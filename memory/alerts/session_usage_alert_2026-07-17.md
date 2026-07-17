# Session Usage Alert

**Date:** 2026-07-17 22:09 UTC
**Status:** 🔴 SESSION_WARN — Above threshold

| Metric | Value |
|--------|-------|
| Usage | **83%** |
| Used | 419 MB |
| Limit | 500 MB |
| Threshold | 80% |

**Recommended Actions:**
1. Run `bash /root/.openclaw/workspace/memory/scripts/bulk_session_cleanup.sh` to prune old sessions
2. Or increase `session.maintenance.maxDiskBytes` in gateway config
3. Or run `smart_session_cleanup.sh` for targeted rotation

**Script result:**
```
⚠️ SESSION_WARN: 83% used (419MB/500MB)
ACTION: Clean old sessions or increase session.maintenance.maxDiskBytes
```
