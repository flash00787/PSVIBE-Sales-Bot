# Project Knowledge Scan — 2026-06-02 13:04 UTC

## Summary
- **Knowledge files:** 5 core files found (PROJECT_STRUCTURE.md, project-state.md, psvibe-code-structure.md, bug-patterns.md, fix-history.md) + 30+ support files in `memory/`
- **Doc accuracy score:** 7/10 — Accurate on current state but has structural gaps
- **Issues found:** 6 documentation gaps, 1 HIGH open bug, 3 MED pending items
- **Shadow docs:** env.example is outdated; no DB schema, no API endpoint doc, no grand opening checklist
- **Git access:** ❌ Sandbox cannot SSH to VPS — git history inferred from memory files only
- **Last known commits:** Bot `941d0a5` (2026-06-02), API batch migration (2026-06-01)

---

## File-by-File Review

### 1. `PROJECT_STRUCTURE.md` ✅ (Good)
- **Status:** Accurate, up-to-date
- **Content:** 2-repo awareness, service listing (sale-bot, customer-bot, API, watchdog), correct file references
- **Gaps:** No database section, no environment variables, no API endpoints list
- **Recommendation:** Minor — add DB schema and env var sections

### 2. `memory/project-state.md` ✅ (Good)
- **Status:** Accurate, last updated for 2026-06-02 fixes
- **Content:** Completed features (session lock, My Booking, confirm→notify, booking↔console link), known issues table, architecture diagram, health scores
- **Accuracy:** Quality Gate 100/100 ✅, Health Monitor 95-97/100 ✅
- **Gaps:** 
  - `sheets/config` migration status says "pending" — actual migration status unclear (some config moved to MySQL, some still GSheet)
  - No grand opening preparation tracker
  - No hard deadlines mentioned beyond the June 6 date

### 3. `memory/psvibe-code-structure.md` ✅ (Good)
- **Status:** Accurate, detailed file-by-file reference
- **Content:** 2-repo with per-file purpose for bot handlers (17 handler files), customer bot (6 files), API server (7 files), architecture
- **Gaps:** 
  - Missing `patch_routes.py` entry (major file added during migration with 10+ function replacements)
  - Missing `receipt_template.html` (custom receipt rendering)
  - Missing `analytics.py` description (listed by name only)
  - `app.py` described as "~2200 lines" — likely now larger after migration fixes

### 4. `memory/bug-patterns.md` ✅ (Excellent)
- **Status:** Well-maintained, 14 documented patterns
- **Content:** Each bug has root cause + fix + lesson learned. Patterns include: Payment cash calc, wallet balance Column H, double multiplier, console URL encoding, Customer Bot menu eat, git push protection, API-bot split awareness, parallel agent collision, crash loop fix, chr() encoding corruption, MySQL-GSheet sync gap, missing comma crash, MarkdownV2 escape, API key mismatch
- **Strengths:** Most complete doc — every fix includes "lesson" which prevents regression
- **Gaps:** None significant. The HIGH open bug (pending bookings display) not yet in patterns

### 5. `memory/fix-history.md` ✅ (Good)
- **Status:** Covers 2026-05-30 to 2026-06-02 with SHA references
- **Content:** 4 days of major fixes with files changed and what was done
- **Gaps:** 
  - Only major fixes — many micro-fixes from daily logs not reflected
  - No rollback markers (which fixes were rolled back or had issues)
  - Migration history only partially covered (detailed migration log in ARCHIVED_LESSONS.md instead)

### 6. Supporting Files Overview

| File | Purpose | Assessment |
|------|---------|------------|
| `memory/infrastructure.md` | VPS arch, coordination tools | ✅ Good — 25+ tools listed |
| `memory/contacts.md` | Boss & colleague info | ✅ Good |
| `memory/config.md` | Config changes (session lock) | ✅ Good |
| `memory/agent-status.md` | Agent dashboard | ✅ Current (2026-06-02 12:38) |
| `GOLDEN_RULES.md` | Core rules | ✅ Excellent |
| `DEPLOY_MANAGER_SOP.md` | Deploy SOP | ✅ Good, structured |
| `ARCHIVED_LESSONS.md` | Historical details | ✅ Useful but should be cleaned |

---

## Git History Summary

> ⚠️ **Cannot access VPS repos directly** — sandbox has no SSH. History below from memory files.

### Sales Bot (`flash00787/PSVIBE-Sales-Bot`)
| Date | SHA | Description |
|------|-----|-------------|
| 2026-06-02 | `941d0a5` | Booking ↔ Console Status Link (Scheduled/Done rows) |
| 2026-06-02 | `6e3c556` | Booking confirm → notify customer + "My Booking" fix |
| 2026-06-01 | `98312ea` | Git state after full audit (100/100 quality gate) |
| 2026-05-31 | multiple | Dynamic payment methods, crash loop fix, button row merge |
| 2026-05-30 | multiple | Payment cash calc, wallet Column H, menu intercept |

### API Server (`flash00787/PSVIBE-API-Server`)
| Date | Description |
|------|-------------|
| 2026-06-01 | All 10 remaining GSheet calls eliminated (22/22 endpoints MySQL) |
| 2026-06-01 | 9 batch patches to `patch_routes.py` + 11 function replacements in `app.py` |
| 2026-06-01 | Backup files: `app.py.bak.migration_20260601_*` |
| 2026-06-01 | sheets_client.py = dead code (zero active GSheet calls) |

### Uncommitted Changes (from daily logs)
- 2026-06-02: Ko VIBE AI system prompt updated in `customer_bot/data/prompts.py` — restart pending
- 2026-06-01: Top-up endpoint restored, rank bonus fixed, receipt template rewritten

---

## Documentation Gaps

### 🔴 CRITICAL GAPS (Pre-Grand Opening Risk)

| # | Gap | Impact | Action Needed |
|---|-----|--------|---------------|
| 1 | **No database schema doc** | No one knows table structures, foreign keys, or MySQL schema without reading Docker logs | CREATE TABLE statements or schema diagram |
| 2 | **No API endpoint documentation** | 22+ endpoints only in code — new sub-agents waste time reverse-engineering | Auto-generate from FastAPI routes |
| 3 | **No environment variables doc** | `.env.example` is **outdated** — shows only `BOT_TOKEN` + `SHEET_ID` from pre-MySQL era. Missing: `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, `SHEET_ID`, `BOT_TOKEN_CUSTOMER`, `RECEIPT_BASE_URL`, `SERVICE_ACCOUNT_PATH` | Comprehensive `.env.example` matching current system |
| 4 | **No grand opening checklist** | 4 days to opening — no disaster recovery plan, no staff runbook, no load testing results | See checklist section below |

### 🟡 MEDIUM GAPS

| # | Gap | Impact | Action Needed |
|---|------|--------|---------------|
| 5 | **MySQL-GSheet sync not documented** | Runs every 5 minutes via cron — but the sync gap (DELETE not synced) is in bug-patterns, not in a deployment/ops doc | Ops note in infrastructure.md or new ops-docs/ |
| 6 | **No service dependency graph** | Service order matters (API → Sale → Customer bot) but only in DEPLOY_MANAGER_SOP | Add to infrastructure.md or PROJECT_STRUCTURE.md |
| 7 | **No rollback procedure doc** | DEPLOY_MANAGER_SOP mentions rollback but no standalone rollback guide | Short rollback SOP |
| 8 | **patch_routes.py not in code structure** | Major file with 10+ endpoint patches — missing from psvibe-code-structure.md | Add entry to code structure doc |

### 🟢 LOW GAPS / Minor Updates

| # | Gap | Action Needed |
|---|------|---------------|
| 9 | `receipt_template.html` not listed in code structure | Add entry |
| 10 | `analytics.py` mentioned but no description | Add 2-line summary |
| 11 | API `app.py` line count stale (~2200 → likely 2500+) | Update line count |
| 12 | MySQL credentials only in archived lessons (ARCHIVED_LESSONS.md) | Move to config.md or secure file |

---

## Pre-Grand Opening Checklist

**Grand Opening:** Saturday, 06 June 2026 — **4 days away**

### ✅ COMPLETED / CONFIRMED

| # | Item | Status | Source |
|---|------|--------|--------|
| 1 | Opening hours confirmed (9AM-9PM) | ✅ | Boss-confirmed, system uses correct values |
| 2 | Pre-opening = testing only | ✅ | Documented in project-state.md |
| 3 | All 3 services running | ✅ | Health monitor confirms |
| 4 | Quality Gate 100/100 | ✅ | Jun 1 full audit |
| 5 | Health Monitor 95-97/100 | ✅ | 5 pillars, hourly checks |
| 6 | Ko VIBE AI prompt updated | ✅ | Chilled gamer persona, shop info embedded |
| 7 | My Booking / customer notifications | ✅ | Jun 2 fix deployed |
| 8 | Booking ↔ Console Status Link | ✅ | Confirm→Scheduled, Cancel→Done |
| 9 | GSheet→MySQL migration (22/22 endpoints) | ✅ | All API endpoints MySQL-backed |
| 10 | Dynamic payment methods | ✅ | Cash, KPay, Wave, CB Pay, etc. |
| 11 | Receipt template (multi-type) | ✅ | new_member, topup, gaming session |

### 🔴 NOT DONE / PENDING (Opening-Day Risks)

| # | Item | Status | Risk Level |
|---|------|--------|------------|
| 1 | **HIGH Bug: Pending bookings not displaying details** | 🔴 Open | **CRITICAL** — Boss can't see who's waiting |
| 2 | **No load test performed** | 🔴 Not done | **HIGH** — unknown if API handles multiple concurrent booking flows |
| 3 | **No opening-day runbook** | 🔴 Not done | **HIGH** — no documented procedure for "first customer" flow |
| 4 | **No disaster recovery plan** | 🔴 Not done | **MED** — what if API crashes on opening day? |
| 5 | **No staff onboarding docs** | 🔴 Not done | **MED** — staff need to know bot commands |
| 6 | **MySQL backup not automated** | 🔴 Not verified | **MED** — is there a daily MySQL dump cron? |
| 7 | **sync_service.py still overwrites spend** | 🟡 Mitigated | **MED** — GSheet re-synced but cron still runs every 5min |
| 8 | **sheets/config still part-GSheet** | 🟡 Pending | **MED** — config partially in MySQL |
| 9 | **No promotional materials in bot** | ⚪ Unknown | **LOW** — opening day promos? |

### ⏱️ Suggested Pre-Opening Sprint (June 2-5)

**Day 1 (Jun 2):** Fix pending bookings HIGH bug → Create opening checklist → Load test API
**Day 2 (Jun 3):** Fix sheets/config migration → Auto-backup MySQL → Create staff runbook
**Day 3 (Jun 4):** Disaster recovery plan → Opening-day promo in Ko VIBE → Final smoke test
**Day 4 (Jun 5):** Opening dress rehearsal → Verify all systems → Team briefing

---

## Known Issues Status

| # | Issue | Priority | Status | Age | Owner |
|---|-------|----------|--------|-----|-------|
| 1 | **Pending bookings display bug — details not showing** | 🔴 HIGH | Open | ~2 days | Unassigned |
| 2 | **MySQL-GSheet sync — DELETE not synced** | 🟡 MED | Known (tracked in bug-patterns) | ~3 days | Known limitation |
| 3 | **sheets/config still partially GSheets (not MySQL)** | 🟡 MED | Migration pending | ~3 days | Pending |
| 4 | **Console ID URL encoding (spaces in "C - 01")** | 🟢 LOW | Known (fallback works) | ~1+ week | Accepted workaround |
| 5 | **sync_service.py overwriting spend (bidirectional sync)** | 🟡 MED | Mitigated (GSheet re-synced) | ~1 day | Ongoing |
| 6 | **API key mismatch data keys** | 🟢 FIXED | ✅ Closed 2026-06-02 | — | Resolved |
| 7 | **Missing comma API crash loop** | 🟢 FIXED | ✅ Closed 2026-06-02 | — | Resolved |
| 8 | **Bot crash loop (KeyError, 703 restarts)** | 🟢 FIXED | ✅ Closed 2026-05-31 | — | Resolved |

### Status Overview
- **Open:** 1 HIGH, 2 MED, 1 LOW = 4 open
- **Closed/Fixed:** 4 resolved
- **Critical for Opening:** Issue #1 (pending bookings display) is the ONLY HIGH blocker

---

## Recommendations

### Urgent (Before June 6)

1. **FIX THE PENDING BOOKINGS BUG** — This is the only HIGH open issue. Boss can't see who's waiting. Invest sub-agents immediately.
2. **CREATE GRAND OPENING CHECKLIST** — Use this report's checklist as a template. Track daily.
3. **WRITE A DATABASE SCHEMA DOC** — Dump CREATE TABLE for all 21+ MySQL tables. Critical for debugging on opening day.
4. **LOAD TEST THE API** — Spawn 10+ concurrent customer bot sessions. Verify API handles load. The migration to MySQL eliminated GSheet latency but introduced new failure modes.

### Medium Priority

5. **UPDATE `.env.example`** — Current one is outdated (pre-MySQL). Add `MYSQL_*`, `RECEIPT_BASE_URL`, `BOT_TOKEN_CUSTOMER`, `SERVICE_ACCOUNT_PATH`.
6. **DOCUMENT ALL 22+ API ENDPOINTS** — Auto-generate from FastAPI route list. Add to `PROJECT_STRUCTURE.md` or `memory/`.
7. **ADD `patch_routes.py` TO CODE STRUCTURE** — It's a major file, should be in `memory/psvibe-code-structure.md`.
8. **AUTOMATE MYSQL BACKUPS** — Verify if `mysqldump` cron exists. If not, create one before opening.

### Routine Housekeeping

9. **UPDATE `app.py` line count** in code structure doc (~2200 → likely 2500+).
10. **MOVE MySQL credentials** from `ARCHIVED_LESSONS.md` to proper secure config file.
11. **CONSOLIDATE ARCHIVED_LESSONS.md** — Migration history is useful but should be in its own doc.
12. **CROSS-CHECK fix-history.md** against daily logs — some May 29-30 micro-fixes missing.

---

## Files Scanned

| # | File | Exists? | Last Known Update |
|---|------|---------|-------------------|
| 1 | `PROJECT_STRUCTURE.md` | ✅ | Pre-2026-06-02 |
| 2 | `memory/project-state.md` | ✅ | 2026-06-02 |
| 3 | `memory/psvibe-code-structure.md` | ✅ | Pre-2026-06-02 |
| 4 | `memory/bug-patterns.md` | ✅ | 2026-06-02 |
| 5 | `memory/fix-history.md` | ✅ | 2026-06-02 |
| 6 | `memory/infrastructure.md` | ✅ | Pre-2026-06-02 |
| 7 | `memory/config.md` | ✅ | 2026-06-02 |
| 8 | `memory/contacts.md` | ✅ | Pre-2026-06-02 |
| 9 | `temp/archive/.../.env.example` | ✅ | Stale (pre-MySQL era) |
| 10 | `memory/DEPLOY_MANAGER_SOP.md` | ✅ | 2026-05-28 |
| 11 | `memory/ARCHIVED_LESSONS.md` | ✅ | 2026-05-31 |
| 12 | `GOLDEN_RULES.md` | ✅ | Pre-2026-06-02 |

---

*Scan performed by subagent. Repos at `/root/psvibe-sales-bot/` and `/root/psvibe_api_server/` inaccessible from sandbox — git state inferred from memory files.*
