# 📖 Memory Usage Guidelines

> How Kora uses the new memory module system.

---

## 🧠 Mental Model: "Books On A Shelf"

```
MEMORY.md  = Card Catalog (ဘယ်စာအုပ်က ဘယ်မှာလဲ ညွှန်တယ် — 56 lines)
memory/    = Bookshelf (စာအုပ်စင် — လိုတဲ့စာအုပ်ကို ဆွဲထုတ်ဖတ်)
```

**အရင်တုန်းက:** MEMORY.md တစ်ခုတည်းမှာ အကုန်ထည့် → ပိလာတယ်
**အခု:** Category အလိုက် သပ်သပ်စီ → လိုတာပဲ ဖွင့်ဖတ်

---

## 📝 When To Write What

### Every Session (Daily Log)
```
memory/YYYY-MM-DD.md   ← Raw events, decisions, conversations
```
- Session မှာ ဘာတွေဖြစ်ခဲ့လဲ — raw log
- Bug, fix, decision, Boss conversation
- Keep it chronological, no filtering

### After A Fix (Immediate — AUTOMATIC, no Boss reminder needed)
```
memory/fix-history.md  ← Append with date + SHA + changes
memory/YYYY-MM-DD.md   ← Append raw events
memory/project-state.md ← Update status if feature/project change
```
- Every fix gets ONE line in fix history
- Example: `| 3 | Booking ↔ Console Link | 941d0a5 | ✅ |`
- Do this after EACH sub-agent completion event, BEFORE next event

### When Pattern Repeats (Move To Module)
```
memory/bug-patterns.md   ← Repeat bug → log pattern
memory/lessons.md        ← Lesson learned → write it down
```
- 2nd time same bug → update bug-patterns.md
- New prevention strategy → update lessons.md

### Rarely Changes (Static Reference)
```
memory/contacts.md       ← Contact info (rarely changes)
memory/emails.md         ← Email accounts (rarely changes)
memory/infrastructure.md ← Architecture (when deployed changes)
memory/config.md         ← Config changes (when edited)
memory/project-state.md  ← Project state (when features ship)
memory/delegation-rules.md ← Helper rules (when SOP changes)
memory/heartbeat-procedures.md ← Heartbeat SOP (when procedure changes)
memory/tools-commands.md ← Commands (when tool added)
memory/psvibe-code-structure.md ← Code ref (when repo structure changes)
```

### MEMORY.md Itself
```
MEMORY.md  ← Only update when new module files are added/removed
```
- This is the CARD CATALOG — only change the index
- Don't put content here, put paths/references

---

## 🔍 How To Find Info

1. **For specific known files:** `memory_get(path=memory/contacts.md)`
2. **For unknown info:** `memory_search(query)` — searches all module files
3. **For session log:** `memory_get(path=memory/YYYY-MM-DD.md)` or check memory/

**သတိထားရန်:** `memory_search` က archive files တွေပါ ရှာမယ် — result မှာ path ကို ကြည့်ပြီး archive ဆိုရင် skip လုပ်

---

## 🔄 Auto-Doc Updater (VPS)

Auto-doc updater က **VPS coordination files တွေကို** update လုပ်တယ်:
- `/root/coordination/KNOWN_BUG_PATTERNS.md` (457 lines, VPS)
- `/root/coordination/FIX_AGENT_SOP.md` (388 lines, VPS)
- Git commit on VPS repos

**Kora's job after auto-doc update:**
1. ✅ Auto-doc updater run (it's done on VPS)
2. 📝 Update workspace files: `memory/fix-history.md` + `memory/YYYY-MM-DD.md`
3. 💾 MEMORY.md index တော့ update မလိုဘူး (module files တွေ ပြောင်းမှသာ)

**The auto-doc updater does NOT touch workspace files** — it only updates VPS coordination doc. So restructuring workspace files doesn't break it.

---

## ✅ Quick Decision Tree

```
New info → ဘယ်မှာထည့်ရမလဲ?
  │
  ├─ Raw conversation / event? 
  │     → memory/YYYY-MM-DD.md (daily log)
  │
  ├─ Bug fix completed?
  │     → fix-history.md + daily log
  │
  ├─ Same bug happening again?
  │     → bug-patterns.md (add pattern)
  │
  ├─ Big lesson / prevention strategy?
  │     → lessons.md
  │
  ├─ Contact / account / infrastructure change?
  │     → Specific module file (contacts, emails, infrastructure)
  │
  ├─ New module file added?
  │     → MEMORY.md (add path to index)
  │
  └─ VPS doc change?
        → auto_doc_updater.py (VPS side, not workspace)
```
