# GOLDEN_RULES.md — Immutable. Violation = Failed Session.
# ═══════════════════════════════════════════════════════════════

## RULE #0 — MONGO FIRST

```
BEFORE any: grep, read, cat, journalctl, ssh (debug), find
YOU MUST:  kora_memory_smart.py trace "<topic>"    # auto-index on miss
           kora_memory_smart.py search "<query>"    # auto-store pending
           kora_memory_smart.py impact "<file>"     # auto-refresh graph
ONLY THEN: grep / read / journalctl
```

**Violations this session:** see AGENTS.md Rule #0 counter
**Penalty:** Boss loses trust. Investment (7,849 entities, 850K relations) wasted.

## RULE #1 — SUB-AGENT DELEGATION

- Code analysis/fix → ALWAYS Pro sub-agent (never direct with Flash)
- Financial numbers, SQL, multi-file → ALWAYS Pro sub-agent
- Never 2 sub-agents targeting same file simultaneously

## RULE #2 — BOSS ALWAYS FIRST

- Boss message → instant response (no quiet hours apply)
- Myanmar Time (UTC+6:30) for all time references
- Burmese language, English technical terms

## RULE #3 — POST-FIX DOCUMENTATION

After every fix:
1. `auto_doc_updater.py --summary "..."`
2. Update daily memory
3. Update MEMORY.md lessons
4. Clean temp files
