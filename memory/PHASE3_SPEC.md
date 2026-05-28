# Kora Memory Upgrade — Phase 3: Complete Spec

## Overview
7 upgrades to make Kora's memory system persistent, searchable, and intelligent.

---

## 1. Session Auto-Summary (`memory/session_summary.py`)
**Goal:** Session ပြီးတိုင်း auto-summary generate လုပ်ပြီး daily log + MEMORY.md ကို update လုပ်မယ်

**Behavior:**
- Reads `memory/session-memory.md` for current session log
- Reads today's daily log (`memory/YYYY-MM-DD.md`)
- Summarizes: key decisions, completed tasks, pending items, important facts
- Appends structured summary to daily log
- `--update-memory` flag: Also writes key insights to MEMORY.md
- `--dry-run`: Preview only

**Output format:**
```
## Session Summary (2026-05-28 09:00-10:00)

### ✅ Completed
- Phase 2 memory upgrade implementation
- Verification of all 12 test steps

### ❌ Pending
- sync-service-create retry needed
- App.py MySQL integration

### 💡 Key Decisions
- Always use Pro model for coding tasks
- Flash model for conversation only

### 📝 Notes
- Boss prefers sequential batch processing
```

---

## 2. Memory Index (`memory/memory_index.py` + `memory/memory-index.json`)
**Goal:** Topic → File mapping. "PS VIBE" ရှာရင် ဘယ် file မှာပါလဲ ချက်ချင်းသိ

**Behavior:**
- Scans all files in `memory/` dir
- Indexes: headings (##), keywords, topics, project names, people names
- Creates searchable `memory/memory-index.json`
- `--rebuild`: Force rebuild full index
- `--search <topic>`: Search and return matching files + line refs

**Index schema:**
```json
{
  "version": 1,
  "updated": "ISO-8601",
  "entries": [
    {
      "topic": "PS VIBE",
      "files": [
        {"path": "MEMORY.md", "line": 15, "context": "PS VIBE - PS5 Gaming Lounge"},
        {"path": "memory/2026-05-28.md", "line": 40, "context": "MySQL integration"}
      ]
    }
  ]
}
```

---

## 3. Priority Memory System (`memory/priority_engine.py`)
**Goal:** Important vs routine — priority ခွဲမယ်။ MEMORY.md ကို auto-manage လုပ်မယ်

**Priority Levels:**
- **P0 (Critical)** — Boss's rules, business decisions, security → Never delete, always in MEMORY.md
- **P1 (Important)** — Project updates, significant events → 30 days in MEMORY.md, then archive
- **P2 (Normal)** — Task completions, routine info → 7 days in daily logs
- **P3 (Transient)** — One-time convos, temp info → 24h then prune

**Behavior:**
- Scans new daily log entries
- Classifies each line/entry by priority
- Auto-promotes to appropriate storage level
- `--classify <text>`: Test classification
- `--audit`: Report current priority distribution

---

## 4. Smart Pruning & Dedup (`memory/memory_pruner.py`)
**Goal:** MEMORY.md ကို clean & lean ဖြစ်အောင်ထားမယ်။ 20K ထက်မကျော်အောင်ထိန်းမယ်

**Behavior:**
- Scans MEMORY.md for duplicate content
- Merges similar entries (fuzzy dedup by line content)
- Archives old P2/P3 entries to `memory/ARCHIVE.md`
- `--dry-run`: Show what would be removed
- `--apply`: Actually perform pruning
- `--target-size <KB>`: Target MEMORY.md size (default 20K)

**Dedup rules:**
- Exact line match → remove duplicate
- Similar lines (>80% match) → merge into one
- Same topic P2/P3 entries → oldest archivable

---

## 5. Daily Digest Generator (`memory/daily_digest.py`)
**Goal:** နေ့ကုန်တိုင်း digest တစ်ခု auto-generate လုပ်ပြီး Boss ဆီ ပို့မယ်

**Behavior:**
- Reads today's daily log
- Categorizes: 💼 Business, 🛠️ Tech, 🎯 Pending, 💡 Decisions
- Formats as clean markdown digest
- Also writes digest to `memory/digests/YYYY-MM-DD-digest.md`
- `--send`: Also output Telegram-ready message

**Output format:**
```
📅 2026-05-28 Daily Digest
├── 💼 Business: MySQL integration partial, bot API in progress
├── 🛠️ Tech: Phase 2 memory upgrade complete
├── 🎯 Pending: sync-service-create retry
└── 💡 Decisions: Pro model for coding
```

---

## 6. Git Auto-Backup (`memory/git_backup.py`)
**Goal:** Memory files တွေကို git repo ထဲ auto-commit လုပ်မယ်

**Behavior:**
- Initializes git repo at `/root/.openclaw/workspace/memory/`
- Creates `.gitignore` (exclude large binary files, temp files)
- `--commit "message"`: Commit all changes with message
- `--auto`: Auto-commit with timestamp message
- `--status`: Show git status summary
- `--log`: Show last 5 commits
- Handles: first init, new files, modified files, untracked
- Uses only stdlib subprocess (git CLI)

**Commit format:** `[KORA MEMORY] YYYY-MM-DD HH:MM - <summary>`

---

## 7. Knowledge Graph (`memory/knowledge_graph.py` + `memory/knowledge-graph.json`)
**Goal:** Topic/People/Project တွေကြားက relationship ကို track မယ်

**Behavior:**
- Scans all memory files for entity relationships
- Nodes: People (Boss, Nova, Ye Yint Oo), Projects (PS VIBE, Synergy Hub), Topics (MySQL, Coding)
- Edges: relationship type + weight
- `--rebuild`: Full rebuild from scratch
- `--graph`: Output node-edge summary
- `--query <entity>`: Show all connections for an entity

**Graph schema:**
```json
{
  "version": 1,
  "nodes": [
    {"id": "boss", "type": "person", "label": "Osmo"},
    {"id": "ps-vibe", "type": "project", "label": "PS VIBE Gaming Lounge"},
    {"id": "mysql", "type": "technology", "label": "MySQL"}
  ],
  "edges": [
    {"source": "boss", "target": "ps-vibe", "relation": "owns", "weight": 5},
    {"source": "ps-vibe", "target": "mysql", "relation": "uses", "weight": 3}
  ]
}
```

---

## File Inventory (New)

| File | Purpose |
|------|---------|
| `memory/session_summary.py` | Auto-summary on session end |
| `memory/memory_index.py` | Topic search index |
| `memory/memory-index.json` | Generated index data |
| `memory/priority_engine.py` | Priority classification |
| `memory/memory_pruner.py` | Dedup & prune |
| `memory/daily_digest.py` | Digest generation |
| `memory/git_backup.py` | Git auto-backup |
| `memory/knowledge_graph.py` | Entity relationship graph |
| `memory/knowledge-graph.json` | Generated graph data |
| `memory/digests/` | Digest output directory |
| `memory/ARCHIVE.md` | Archived old entries |
