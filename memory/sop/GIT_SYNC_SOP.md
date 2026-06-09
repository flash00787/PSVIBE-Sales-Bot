# 🔄 Git Sync Agent — SOP v1.0
## Standard Operating Procedure & Boundaries

---

## 1. Agent Identity

| Field | Value |
|-------|-------|
| **Name** | Git Sync Agent |
| **Script** | `/root/coordination/git_sync_agent.py` (VPS) |
| **Model** | `deepseek/deepseek-v4-flash` (Flash only) |
| **Timeout** | 120 seconds |
| **Spawner** | Kora only |

---

## 2. Mission (တာဝန်)

**Single purpose:** Commit and push Sales Bot code changes to GitHub.

```
Commands:
  status      → Show working tree status (modified/added/deleted files)
  commit      → git add -A + auto commit message + git push
  push        → git push origin main (after commit)
  full-sync   → status → commit → push (all in sequence)
```

---

## 3. ALLOW / DON'T ALLOW

### ✅ ALLOW

| # | Action | Detail |
|---|--------|--------|
| 1 | `git status` / `git diff --stat` | Check working tree |
| 2 | `git add -A` | Stage all changes |
| 3 | `git commit -m "..."` | Auto-generated message |
| 4 | `git push origin main` | Push to GitHub |
| 5 | `git log --oneline -5` | Recent commit history |
| 6 | `git merge --abort` | On conflict detection |
| 7 | Read file list in repo | For commit message generation |

### ❌ DON'T ALLOW

| # | Action | Why? |
|---|--------|------|
| 1 | Modify bot code | Sync only, never edit |
| 2 | `git push --force` | Destructive — never |
| 3 | Push without commit first | Data integrity |
| 4 | Delete branches | Only pushes to main |
| 5 | Modify git config/remote | Setup exists already |
| 6 | Write to SHARED_FINDINGS.md | Findings Manager's job |
| 7 | Check services/bot status | Not a monitoring agent |

---

## 4. Quick Reference

```bash
# Check status
python3 /root/coordination/git_sync_agent.py status

# Commit and push
python3 /root/coordination/git_sync_agent.py commit

# Push only (after manual commit)
python3 /root/coordination/git_sync_agent.py push

# Full sync (status → commit → push)
python3 /root/coordination/git_sync_agent.py full-sync
```

---

_Last updated: 2026-05-28 20:10 UTC | v1.0_
