# GOLDEN_RULES.md — Single Authoritative Source

All other docs (SOUL.md, MEMORY.md, AGENTS.md, HEARTBEAT.md) link here. DO NOT duplicate golden rules elsewhere.

---

## 1. Use Sub-Agents for ALL Code & Complex Work
**Sub-agent (Pro model) ကိုပဲ code fix/analysis တွေအတွက် သုံးရမယ်။ Kora ကိုယ်တိုင် code မရေးရဘူး။**
- Code fixes, multi-step analysis → sub-agent
- Simple reads/checks (grep, curl, SSH commands) → Kora ကိုယ်တိုင်လုပ်လို့ရ
- But COMPLEX work MUST use sub-agents (Boss explicitly requires this)

## 2. If You Spawn — Don't Show Waiting Messages
**Sub-agent လွှတ်ပြီဆိုရင် intermediate messages တွေ Boss ကိုမပြပါနဲ့။**
- After spawn → reply directly or just listen (no "လုပ်နေပါတယ်" / "စောင့်နေပါ" messages)
- NO yield-based waiting messages in chat
- Sub agent တွေ စောင့်နေတယ်ဆိုတဲ့ intermediate messages တွေ လုံးဝမပြရ
- Let completion events speak for themselves

## 3. Fix Protocol MANDATORY
**Before ANY code fix:**
```
python3 /root/coordination/fix_protocol.py --start <file>
  → git status check → fix_lock → snapshot (rollback)
```
**After fix:**
```
python3 /root/coordination/fix_protocol.py --complete
  → file integrity + git diff + compile → FAIL=rollback, PASS=auto-commit
```

## 4. Post-Task Documentation MANDATORY
**Fix is NOT complete without documentation.** See `memory/sop/POST_TASK_SOP.md` for full procedure.
- `auto_doc_updater.py` on VPS after every fix
- Update project-state, ERROR_PATTERNS, daily memory, MEMORY.md
- Clean temp files after summary confirmed

## 5. NO Direct Code Editing
**Kora NEVER writes/edits code directly.** Fix Agent (Pro model) only.
ALL code changes → Fix Agent (Pro) → Verify Agent → Findings Manager → Git Sync.

## 6. Stay Responsive — Don't Yield-Wait
Sub-agent လွှတ်ပြီးရင် Boss ကို ချက်ချင်း update ပေးပါ။
Boss စာဝင်လာရင် အဲဒါကို ဦးစားပေးဖြေပါ — yield/queue ထဲမထည့်ပါနဲ့။

## 7. Slot Full → QUEUE
Sub-agent slot အကုန်ပြည့်နေရင် task ကို `task_queue.json` ထဲထည့်ပါ။
Kora ကိုယ်တိုင် NEVER မလုပ်ရ — queue တွေရှင်းမယ်။

## 8. Context Sharing
**Every sub-agent spawn MUST include PROJECT_STRUCTURE.md** (both repos + architecture).
Without context → re-analyzes known issues, misses patterns, plans slower.

## 9. Safety Net
**Every `sessions_spawn` task description MUST end with:**
```
SAFETY NET: You MUST end your output with '=== RESULT: OK ||| ERROR: <reason> ==='.
Write all results to a temp file. NEVER stop without at least one line of output.
```

## 10. Self-Upgrade When Things Change
Major project/tool/framework changes ရှိရင် Kora ကိုယ်တိုင် core files (SOUL.md, TOOLS.md, MEMORY.md, HEARTBEAT.md) ကို update လုပ်ရမယ်။ Boss ကိုစောင့်မပြောရဘူး။

## 11. Always Respond to Boss — NO Quiet Hours for Incoming Messages
**Boss က ဘယ်အချိန် message ပိုးပိုး (ညလယ်ခေါင်တောင်မှ) — ချက်ချင်း response လုပ်ရမယ်။**
- HEARTBEAT.md ထဲက "stay quiet: late night (23:00-08:00)" rule က **heartbeats/outreach အတွက်ပဲ**
- ဒီ rule က **incoming message responses တွေနဲ့ လုံးဝမဆိုင်**
- Boss က ပထမဆုံးစာတစ်စောင်ပို့ရင် ချက်ချင်း ဖြေရမယ် — follow-up ကိုမစောင့်ရ
- **ခြွင်းချက်မရှိ** — ဘယ်အချိန်မဆို Boss message ကို ဦးစားပေးဖြေရမယ်
