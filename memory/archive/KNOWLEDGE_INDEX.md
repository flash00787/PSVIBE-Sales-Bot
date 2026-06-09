# 📚 Kora Knowledge Base Index

> **Last Updated:** 2026-05-30 15:52 UTC
> **Location:** `/home/node/.openclaw/workspace/`

---

## 🔴 Golden Rule (2026-05-29 — ABSOLUTE)

> **Kora NEVER does ANY work manually. Zero exceptions.**
> Agent slots full → **WRITE to `temp/task_queue.json`** → NEVER do it yourself.
> Manual work = skips safety checks = bugs = wasted time.

---

## 🧠 Core Identity Files

| File | Purpose | When to Read |
|------|---------|-------------|
| **SOUL.md** | Who Kora is, tone, golden rules, delegation templates | Every session start |
| **IDENTITY.md** | Quick identity reference (name, avatar, boss) | When asked who you are |
| **USER.md** | About Boss (name, preferences, business) | Context for any Boss interaction |
| **AGENTS.md** | Workspace rules, memory, security, heartbeat conventions, **helper-first reflex rule** | Every session start — re-read reflex rule section |

---

## 🛠️ Operations & Tools

| File | Purpose | When to Read |
|------|---------|-------------|
| **TOOLS.md** | SSH hosts, API keys, project locations, contact list | Before SSH, sending messages, accessing projects |
| **OPS_REFERENCE.md** | All VPS commands — tools, services, tests, SOP docs | Before running any VPS operation |
| **HEARTBEAT.md** | Periodic tasks checklist, helper decision tree | Every heartbeat |
| **ERROR_PATTERNS.md** | Known error patterns and fixes | When encountering any error |

---

## 🚨 Startup Enforcement

**At EVERY session start, boot_protocol.py shows:**
1. ✅ Helper reflex reminder
2. ✅ Active projects + last session
3. ✅ Pending tasks/notifications

**Golden Reflex Rule:** Task တစ်ခုခု Boss ဆီက ရောက်လာတာနဲ့ — ချက်ချင်း check: "helper ရှိလား?" → ရှိရင် helper ခေါ် → မရှိမှ Task Planner ခေါ်။

---

## 💾 Memory

| File | Purpose | When to Read |
|------|---------|-------------|
| **MEMORY.md** | Long-term curated memory (decisions, events, lessons) | Main session start |
| **memory/YYYY-MM-DD.md** | Daily raw logs | When reviewing a specific day |
| **memory/heartbeat-state.json** | Last heartbeat status | During heartbeat |

---

## 📊 Project State

| File | Purpose | When to Read |
|------|---------|-------------|
| **project-state/psvibe-sales-bot.md** | PS VIBE project status, todo, blockers | When working on PS VIBE |
| **project-state/session-tracker-last.md** | Last session state, open threads, config changes | Every session start |

## 🏗️ Bot Structure References

| File | Size | Purpose |
|------|------|---------|
| **references/sales_bot_handlers.md** | 34K | Complete handler/button flow audit (27 handlers) |
| **references/LOGIC_FLOW_AUDIT.md** | 7K | Architecture overview + dual data path diagram |
| **references/sales_bot_completeness.md** | 13K | Completeness audit — all fix items resolved |
| **references/customer_bot_audit.md** | 18K | Customer bot full audit (46 functions, 3 bugs fixed) |
| **references/sales_bot_member_flow.md** | 19K | Member flow audit |
| **references/sales_bot_book_stock.md** | 22K | Book/stock flow audit |
| **references/sales_bot_finance_staff.md** | 11K | Finance/staff audit |
| **references/sales_bot_api_sheet.md** | 22K | API ↔ Sheet mapping audit |

---

## 📜 VPS SOP Documents (at `/root/coordination/`)

| File | Purpose | When to Read |
|------|---------|-------------|
| **FIX_AGENT_SOP.md** | Fix procedure rules | Before spawning any Fix Agent |
| **DEV_TEAM_SOP.md** | Dev team roles & workflow | Before complex fixes |
| **MULTI_PASS_PROTOCOL.md** | 3-pass fix strategy | Before multi-step fixes |
| **CODEBASE_CONTEXT.md** | Project structure & conventions | Before code changes |
| **KNOWN_BUG_PATTERNS.md** | Past incident patterns | Before fixes (prevent repeats) |

---

## 🔐 Secrets (DO NOT SHARE)

| Resource | Location |
|----------|----------|
| Gmail OAuth | `/home/node/.openclaw/workspace/token.json` |
| SSH Key | `/home/node/.openclaw/workspace/.ssh/id_rsa` |
| Kora Drive SA | `/home/node/.openclaw/workspace/kora_drive_sa.json` |

---

## 🔄 Session Startup Checklist

1. Read `SOUL.md` → identity, delegation, golden rules
2. Read `AGENTS.md` → workspace rules
3. Read `session-tracker-last.md` → where we stopped
4. Read `MEMORY.md` → long-term context
5. Check `project-state/psvibe-sales-bot.md` → current project status
6. If heartbeat: read `HEARTBEAT.md` → periodic tasks
7. **NEW:** Check pending pipeline notifications → `ssh root@5.223.81.16 python3 /root/coordination/notifier.py list --unread`
8. **NEW:** Check pending sub-agent tasks → `ssh root@5.223.81.16 python3 /root/coordination/task_bridge.py list pending`

---

*Auto-generated: 2026-05-29*
