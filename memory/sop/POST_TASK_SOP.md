# POST_TASK_SOP.md — Post-Task Documentation Procedure

> Single authoritative source. Other docs (SOUL.md, MEMORY.md, AGENTS.md, HEARTBEAT.md) link here.

---

## After EVERY task completion (AUTOMATIC — no Boss reminder needed)

### 🔴 MANDATORY — MUST do after every fix:

| # | Step | Where | How |
|---|------|-------|-----|
| 1 | **auto_doc_updater** (VPS) | VPS coordination | `python3 /root/coordination/auto_doc_updater.py --summary "Fixed X: ..."` |
| 2 | **fix-history.md** | `memory/fix-history.md` | Append: `| # | Feature | SHA | Status |` row |
| 3 | **Daily log** | `memory/YYYY-MM-DD.md` | Append raw events + SHA |
| 4 | **project-state.md** | `memory/project-state.md` | Update status if feature completed/issue resolved |
| 5 | **Clean temps** | `temp/` | Delete `.txt` files after summary confirmed |
| 6 | **Long-term memory** | If significant lesson → `memory/lessons.md` | If new bug pattern → `memory/bug-patterns.md` |

### ⏱️ When:
- **After processing each sub-agent completion event** (before moving to next event)
- **Sequential** — one at a time, never parallel (prevents conflict)

### 🚫 What NOT to update automatically:
- `MEMORY.md` (index) — only when new module files added/removed
- `memory/infrastructure.md` — only when architecture changes
- `memory/psvibe-code-structure.md` — only when repo structure changes

---

## Documentation consequence if skipped:
Fix marked incomplete, bug patterns unrecorded → same bug recurs. Boss will notice.

---

## Every sub-agent task description MUST include:

```
DOCUMENTATION: After fix verified, ALWAYS:
1. python3 /root/coordination/auto_doc_updater.py --summary "<what you fixed>"
```
