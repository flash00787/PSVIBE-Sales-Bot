# 🔧 Config Changes

## Session Lock Timeout Fix (2026-06-02)
**File:** `/home/node/.openclaw/openclaw.json`

| Key | Before | After |
|-----|--------|-------|
| `session.writeLock.acquireTimeoutMs` | 60000 (60s) | **300000 (5 min)** |
| `session.maintenance.mode` | warn | **enforce** |
| `session.maintenance.maxDiskBytes` | unlimited | **314572800 (300mb)** |
| `session.maintenance.pruneAfter` | — | **7d** |
| `session.maintenance.resetArchiveRetention` | — | **2d** |

## Lock Monitor Updates (2026-06-02)
**File:** `/home/node/.openclaw/workspace/memory/lock_monitor.py`

| Key | Before | After |
|-----|--------|-------|
| `SESSION_MAX_AGE_DAYS` | 7 | **2** |
| `TRAJECTORY_MAX_AGE_DAYS` | 7 | **2** |
| `TRAJECTORY_MAX_SIZE_KB` | 5000 | **3000** |
| `TRAJECTORY_FORCE_CLEAN_KB` | — | **10000** (new) |

## Fix Protocol (MANDATORY before any code change)
```bash
# Start
python3 /root/coordination/fix_protocol.py --start <file>
  → git status check → fix_lock → snapshot (rollback)

# Complete
python3 /root/coordination/fix_protocol.py --complete
  → file integrity + git diff + compile → FAIL=rollback, PASS=auto-commit
```
