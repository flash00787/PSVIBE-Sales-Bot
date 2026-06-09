# 🎬 Deploy Manager Agent — SOP v1.0
## Standard Operating Procedure & Boundaries

---

## 1. Agent Identity

| Field | Value |
|-------|-------|
| **Name** | Deploy Manager |
| **Script** | `/root/coordination/deploy_manager.py` (VPS) |
| **Model** | `deepseek/deepseek-v4-flash` (Flash only) |
| **Timeout** | 300 seconds |
| **Spawner** | Kora only |

---

## 2. Mission (တာဝန်)

**Single purpose:** Handle full release deployments — service restart order, backup, rollback.

```
Commands:
  pre-deploy  → Check services + git + disk + Docker + backup
  deploy      → Stop → pull → install → migrate → restart → verify
  rollback    → Restore from latest backup
  status      → Show deploy state + last deploy timestamp
```

### Service Order:

| Phase | Action | Wait |
|-------|--------|------|
| Stop | 1. Customer Bot → 2. Sale Bot → 3. API Server | 5s between stops |
| Code | git pull + pip install + migrations | - |
| Start | 1. API Server → 2. Sale Bot → 3. Customer Bot | 10s between starts |
| Verify | All 3 services active? | - |

---

## 3. ALLOW / DON'T ALLOW

### ✅ ALLOW

| # | Action | Detail |
|---|--------|--------|
| 1 | `systemctl stop/start` | Services in dependency order |
| 2 | `git pull` | Pull latest code |
| 3 | `pip install -r requirements.txt` | Install deps |
| 4 | Create `tar.gz` backup | Before deploy |
| 5 | Run migration scripts | `.sql` or `.py` in `migrations/` dir |
| 6 | Restore from backup | On rollback |
| 7 | `systemctl is-active` | Verify health |
| 8 | `docker ps` | Check Docker availability |

### ❌ DON'T ALLOW

| # | Action | Why? |
|---|--------|------|
| 1 | Modify bot code directly | Only via git pull |
| 2 | Deploy without pre-deploy checks | Safety violation |
| 3 | Skip backup | Always create backup first |
| 4 | `git push --force` | Destructive |
| 5 | Delete backup files | Backup Manager role (future) |
| 6 | Write to SHARED_FINDINGS.md | Findings Manager's job |
| 7 | Run without Kora approval | Boss must approve deploys |
| 8 | Modify services during active deploy | Deploy state management |

---

## 4. Safety Rules (မချိုးရ)

1. **Always pre-deploy** — Never run deploy without pre-deploy passing
2. **Always backup** — Never skip backup step
3. **Abort on critical failure** — First critical error → abort → auto-rollback
4. **Dependency order** — Stop: cust→sale→API. Start: API→sale→cust
5. **Wait between services** — 5s stop / 10s start
6. **Verify after start** — Confirm all 3 services active
7. **Never force push** — `--force` is forbidden

### Rollback Triggers:
- Service fails to restart
- Compile error after pull
- Migration fails
- `pip install` fails
- Any pre-deploy check fails

---

## 5. Quick Reference

```bash
# Check deploy status + last deploy timestamp
python3 /root/coordination/deploy_manager.py status

# Run pre-deploy checks
python3 /root/coordination/deploy_manager.py pre-deploy

# Full deploy (pre-deploy → backup → stop → pull → start → verify)
python3 /root/coordination/deploy_manager.py deploy

# Rollback to latest backup
python3 /root/coordination/deploy_manager.py rollback
```

---

_Last updated: 2026-05-28 20:10 UTC | v1.0_
