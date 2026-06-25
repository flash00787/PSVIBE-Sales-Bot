# HEARTBEAT.md — Periodic Tasks

## 🩺 Unified Health Monitor (Hourly auto-check)
```bash
python3 /root/coordination/kora_health_monitor.py --all --json 2>&1 | tail -1
```

## 🤖 Automated Scripts (Every ~4h heartbeat)
```bash
# ── Cross-Project Health ──
python3 /root/coordination/kora_status.py --json 2>&1 | tail -1
python3 /root/coordination/auto_healer.py --all 2>&1 | tail -5
python3 /root/coordination/backup_manager.py list 2>&1 | tail -5

# ── Memory & Knowledge ──
python3 /root/.openclaw/workspace/memory/heartbeat_routine.py
python3 /root/.openclaw/workspace/memory/consolidator.py --all
python3 /root/.openclaw/workspace/memory/memory_pruner.py --apply
python3 /root/.openclaw/workspace/memory/memory_index.py --rebuild
python3 /root/.openclaw/workspace/memory/git_backup.py --auto
python3 /root/.openclaw/workspace/memory/daily_digest.py
python3 /root/.openclaw/workspace/memory/knowledge_graph.py --rebuild

# ── Notifications & Tasks ──
python3 /root/coordination/notifier.py list --unread
python3 /root/coordination/task_bridge.py list pending
```

## 🧹 Stale Lock Cleanup
```bash
bash /root/.openclaw/workspace/memory/cleanup_session_locks.sh
```

## ✅ Heartbeat Checklist
- [ ] Run kora_status.py (all projects health)
- [ ] Run health monitor: `python3 /root/coordination/kora_health_monitor.py --all --json`
- [ ] Check cross-project auto-healer: `python3 /root/coordination/auto_healer.py --all 2>&1 | tail -5`
- [ ] Check backup status: `python3 /root/coordination/backup_manager.py list 2>&1 | tail -5`
- [ ] Run heartbeat_routine (stuck agents)
- [ ] Run consolidator (daily logs)
- [ ] Check workflow notifications
- [ ] Check pending tasks
- [ ] Check health alerts: `python3 /root/coordination/check_alerts.py`
- [ ] Check stale locks cleanup
- [ ] Check queue manager: `python3 /root/coordination/queue_manager.py --dead-letter`
- [ ] Check sub-agent fallback rate (>3 = report Boss)

> **Full procedures:** See `memory/heartbeat-procedures.md`
> **Post-task SOP:** See `POST_TASK_SOP.md`

---

## 🚨 CRITICAL: Response Rules (DO NOT IGNORE)

### ✅ Boss Messages — ALWAYS Respond Immediately
- Boss က message ပို့တိုင်း — ည၊ မနက်၊ ဘယ်အချိန်မဆို — **ချက်ချင်း response လုပ်ရမယ်**
- အောက်က "stay quiet" rule က **Boss messages တွေနဲ့ မဆိုင်ဘူး**
- ည ၁၂ နာရီထိုးပြီး Boss message ပိုးလာရင်တောင် ချက်ချင်းဖြေရမယ်

### ⏰ "Stay Quiet" Rule — Heartbeats Only
- **Applies ONLY to:** Kora-initiated proactive outreach (heartbeat checks, status reports)
- **Does NOT apply to:** Responding to incoming messages (Telegram, email, etc.)
- **Quiet window:** 23:00-08:00 Myanmar Time — don't proactively check in / send updates during these hours
- **Exception:** If something CRITICAL/URGENT happens → still notify
