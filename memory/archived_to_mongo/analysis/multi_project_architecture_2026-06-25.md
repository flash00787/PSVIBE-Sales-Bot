# Kora Multi-Project Architecture Analysis
> **Date:** 2026-06-25 02:15 UTC  
> **Author:** Kora Sub-Agent (DeepSeek Pro)  
> **Scope:** Full infrastructure audit for adding Project #2+ beyond PS VIBE

---

## Executive Summary

Kora currently manages **1 primary project** (PS VIBE) with **83% of coordination tools hardcoded** to PS VIBE paths and service names. There are already **5 other isolated projects** running on the same VPS (`construction-bot`, `YYO wallet`, `ACM wallet`, `kora-voice`, `social_auto_reply`), but none of them benefit from Kora's coordination system. Adding a second Kora-managed project will require a **project abstraction layer** — without it, every coordination tool, validator, deployer, and health monitor will break or silently operate on the wrong project.

**Bottom line:** Kora is currently a **single-project orchestrator** pretending to be multi-project. The DB has branch support, but the coordination tools have zero project-awareness.

---

## 1. Problem Diagnosis — What Will Break If We Add Project #2

### 🔴 Critical Breakage (Immediate Failures)

| Component | What Breaks | Severity |
|-----------|------------|----------|
| **auto_healer.py** | `SERVICES = ["psvibe-sale-bot", "psvibe_customer_bot", "psvibe-api"]` — only monitors PS VIBE | 🔴 Critical |
| **validate.py** | `SERVICES = [("Sale Bot", "psvibe-sale-bot.service"), ...]` — only validates PS VIBE | 🔴 Critical |
| **preflight.py** | `chk_svc()` only checks psvibe services; `BD = "/root/psvibe-sales-bot"` hardcoded | 🔴 Critical |
| **workflow_engine.py** | `PROJECT = "/root/psvibe-sales-bot"` hardcoded; all pipelines operate on PS VIBE only | 🔴 Critical |
| **deploy_manager.py** | `BASE_DIR = Path("/root/psvibe-sales-bot")` — can't deploy anything else | 🔴 Critical |
| **git_sync_agent.py** | `REPO_PATH = "/root/psvibe-sales-bot/"` — only pushes PS VIBE to GitHub | 🔴 Critical |
| **health_dashboard.py** | `PROJECT = "/root/psvibe-sales-bot"` + only checks `psvibe-*` services | 🔴 Critical |
| **auto_git_sync.py** | `PROJECT_DIR = "/root/psvibe-sales-bot"` — only syncs PS VIBE | 🔴 Critical |
| **auto_verify.py** | `PROJECT_DIR = "/root/psvibe-sales-bot"` — only verifies PS VIBE | 🔴 Critical |
| **fix_protocol.py** | `WORKSPACE = "/root/psvibe-sales-bot"` — can't start fix protocol on other projects | 🔴 Critical |
| **fix_safety.py** | Hardcoded service list: `"psvibe-sale-bot.service", "psvibe_customer_bot.service", "psvibe-api.service"` | 🔴 Critical |
| **integration_tester.py** | All 7 test commands reference `psvibe-*` services and paths | 🔴 Critical |
| **status_reporter.py** | Only reports PS VIBE health (6 refs) | 🔴 Critical |
| **batch_coordinator.py** | `WORKSPACE = "/root/psvibe-sales-bot"`, `CRITICAL_FILES` are all psvibe paths | 🔴 Critical |
| **kora_health_monitor.py** | Only checks `psvibe-*` services and `psvibe-sales-bot` repos | 🔴 Critical |

### 🟡 Will Partially Work (Incomplete/Confusing)

| Component | Issue |
|-----------|-------|
| **arch_mapper.py** | Default `--bot-dir=/root/psvibe-sales-bot` — works if passed correct flag, but defaults wrong |
| **flow_analyzer.py** | All defaults point to psvibe paths — needs CLI override every time |
| **enhanced_validator.py** | Same — defaults to psvibe dir |
| **import_scanner.py** | `project_roots = ['/root/psvibe-sales-bot', '/root/psvibe_api_server']` hardcoded |
| **auto_doc_updater.py** | Scans `["/root/psvibe-sales-bot", "/root/coordination"]` — won't update docs for new projects |
| **dashboard.py** | Backup glob: `psvibe_*.sql.gz`, bot paths hardcoded |
| **rollback.py** | References psvibe services in rollback commands |
| **spawning_manager.py** | Validates psvibe-specific services |
| **lock_manager.py** | Lock path mapping only knows `bot/`, `customer_bot/`, `api_server/` → psvibe paths |

### 🟢 No Impact (Generic Tools)

| Component | Why Safe |
|-----------|----------|
| **findings_manager.py** | 0 psvibe refs — pure filesystem ops |
| **merge_findings.py** | 0 psvibe refs — pure JSON merge |
| **lock_monitor.py** | 0 psvibe refs |
| **queue_manager.py** | 0 psvibe refs |
| **task_bridge.py** | 0 psvibe refs |
| **tool_orchestrator.py** | 0 psvibe refs — runs other tools generically |
| **check_alerts.py** | 0 psvibe refs |
| **validate_contracts.py** | 0 psvibe refs |

---

## 2. Current Pain Points — What's Already Messy

### 2.1 Path Hardcoding Epidemic (174 instances across 43 tools)

```
Top offenders (psvibe reference count):
  auto_fix_monitor.py     18 references
  batch_coordinator.py    15 references
  service_watchdog.py     12 references
  deploy_manager.py       11 references
  workflow_engine.py       7 references
  fix_lock.py              7 references
  verify_agent.py          6 references
  status_reporter.py       6 references
  integration_tester.py    6 references
  health_dashboard.py      5 references
  flow_analyzer.py         5 references
  arch_mapper.py           5 references
```

### 2.2 Service Name Fragmentation

Systemd service naming is inconsistent even **within PS VIBE**:
- `psvibe-sale-bot` (with dashes)
- `psvibe_customer_bot` (with underscores)
- `psvibe-api` (short form)
- `psvibe-analytics` (dash)
- `psvibe-attendance` (dash)
- `psvibe-discord-bot` (dashes)
- `psvibe-watchdog` (dash)
- `psvibe-social-autoreply` (dashes)

No naming convention. If Project #2 follows a different pattern, all service checks break.

### 2.3 Project Detection Is Manual

There is **zero** automatic project detection. Kora's AGENTS.md context always assumes PS VIBE. Every tool defaults to PS VIBE paths. There is no:
- `$PROJECT` environment variable
- `projects.json` registry
- Auto-detection from current working directory
- `--project` flag on any tool

### 2.4 Already-Running Orphan Projects

5 projects already run on the VPS with NO Kora coordination:
| Project | Path | Service | Kora Aware? |
|---------|------|---------|-------------|
| Construction Bot | `/opt/construction-bot/` | Docker | ❌ No |
| YYO Personal Wallet | `/opt/yyo-personal-wallet/` | `yyo-personal-wallet.service` | ❌ No |
| ACM Personal Wallet | `/root/ACM-Personal-Wallet/` | `acm-personal-wallet.service` | ❌ No |
| Kora Voice | `/opt/kora-voice/` | `kora-voice.service` | ❌ No (Kora service, but not coordinated) |
| Social Auto Reply | `/opt/social_auto_reply/` | `psvibe-social-autoreply.service` | ❌ No |

These have:
- No deployment pipeline
- No health monitoring
- No auto-healing
- No git sync
- No fix protocol
- No quality gates

### 2.5 Database Isolation Is Already Partially Broken

The `psvibe-mysql` container hosts the `psvibe_api` database. The `branch_id` column was added (June 22) for multi-branch, but:
- `branch_context_middleware` exists but **endpoints don't filter by branch_id** (known issue from audit)
- Dashboard `client.ts` has no branch header support
- Dashboard branch selector UI not built
- No separate DB user per project — everything shares `psvibe_api`

### 2.6 Memory & Knowledge Isolation — None

All of Kora's memory lives in a single flat structure:
- `MEMORY.md` — 90% PS VIBE content
- `memory/*.md` — all PS VIBE context
- `AGENTS.md` — PS VIBE-centric rules
- `TOOLS.md` — PS VIBE-heavy commands
- No project-scoped memory isolation anywhere

---

## 3. Target Architecture — Multi-Project Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                        KORA ORCHESTRATION LAYER                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  project_registry.json   ← single source of truth             │  │
│  │  kora_context_switch.py  ← detect which project Boss means     │  │
│  │  coordination/*.py       ← --project flag on all tools        │  │
│  └───────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  PS VIBE      │     │  Project #2   │     │  Project #3   │
│  (primary)    │     │  (future)     │     │  (future)     │
├───────────────┤     ├───────────────┤     ├───────────────┤
│ Code:         │     │ Code:         │     │ Code:         │
│ /root/psvibe- │     │ /opt/<proj>/  │     │ /opt/<proj>/  │
│ sales-bot/    │     │               │     │               │
│ /root/psvibe_ │     │               │     │               │
│ api_server/   │     │               │     │               │
├───────────────┤     ├───────────────┤     ├───────────────┤
│ Services:     │     │ Services:     │     │ Services:     │
│ psvibe-*      │     │ <proj>-*      │     │ <proj>-*      │
├───────────────┤     ├───────────────┤     ├───────────────┤
│ DB:           │     │ DB:           │     │ DB:           │
│ psvibe-mysql  │     │ <proj>-mysql  │     │ <proj>-mysql  │
│ psvibe_api    │     │ <proj>_db     │     │ <proj>_db     │
├───────────────┤     ├───────────────┤     ├───────────────┤
│ Memory:       │     │ Memory:       │     │ Memory:       │
│ memory/       │     │ memory/proj/  │     │ memory/proj/  │
│ psvibe/       │     │ <proj>/       │     │ <proj>/       │
├───────────────┤     ├───────────────┤     ├───────────────┤
│ Kora Context: │     │ Kora Context: │     │ Kora Context: │
│ Always active │     │ On mention    │     │ On mention    │
└───────────────┘     └───────────────┘     └───────────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   SHARED INFRA      │
                    │  ┌───────────────┐  │
                    │  │ Docker Engine  │  │
                    │  │ Caddy Reverse  │  │
                    │  │ Cloudflare Tun │  │
                    │  │ Fail2Ban       │  │
                    │  │ SSH/System     │  │
                    │  │ MySQL Server   │  │
                    │  │ n8n            │  │
                    │  └───────────────┘  │
                    │                     │
                    │  Kora coordination/ │
                    │  tools (project-    │
                    │  aware)             │
                    └─────────────────────┘
```

---

## 4. Project Isolation Strategy

### 4.1 File Layout Standard

Every Kora-managed project follows this structure:

```
/opt/<project-slug>/           ← PROJECT_ROOT ($PROJECT_DIR)
├── code/                      ← source code (or project root itself)
├── PROJECT_MANIFEST.yaml      ← metadata (required)
├── docker-compose.yml         ← if Docker-based
├── .git/                      ← git repo
│
# Or if in /root:
/root/<project-slug>/
├── ... same structure ...
├── PROJECT_MANIFEST.yaml
```

### 4.2 PROJECT_MANIFEST.yaml (Required per project)

```yaml
# /opt/<project-slug>/PROJECT_MANIFEST.yaml
project:
  slug: "construction"
  name: "Three Brothers Construction Bot"
  owner: "Ko Aung Chan Myint"
  github: "flash00787/construction-bot"
  type: "telegram-bot"          # telegram-bot | web-app | api | discord-bot | automation
  language: "nodejs"            # python | nodejs | mixed

paths:
  code_root: "/opt/construction-bot"
  entry_point: "bot.js"
  env_file: "/etc/construction/secrets.env"   # optional

services:
  - name: "construction-bot"
    unit: "construction-bot.service"    # systemd unit name (optional, for Docker-based)
    type: "docker"                      # docker | systemd
    container: "construction_bot"       # Docker container name

database:
  host: "127.0.0.1"
  port: 3306
  name: "construction_db"
  user: "construction_user"
  container: "construction-mysql"      # if separate container

coordination:
  deploy_branch: "main"
  backup_globs: ["/root/backups/construction_*.tar.gz"]
  critical_files: ["bot.js", "setup-sheet.js"]
  test_command: "node --check bot.js"  # or "python3 -m pytest"
  health_check: "docker ps --filter name=construction_bot --format '{{.Status}}'"

memory:
  knowledge_dir: "memory/projects/construction/"
```

### 4.3 Naming Convention (Mandatory)

```
Service names:    <project-slug>-<component>         (lowercase, dashes only)
  Example:        psvibe-sale-bot, construction-bot, yyo-wallet
  Bad:            psvibe_customer_bot (underscore) → MUST migrate
  
Database names:   <project-slug>_db
  Example:        psvibe_db, construction_db
  
Database users:   <project-slug>_user
  Example:        psvibe_user, construction_user
  
MySQL containers: <project-slug>-mysql
  Example:        psvibe-mysql, construction-mysql
  
Backup files:     <project-slug>_backup_<timestamp>.tar.gz
  Example:        psvibe_backup_20260625_0215.tar.gz
  
Memory files:     memory/projects/<project-slug>/
  Example:        memory/projects/psvibe/, memory/projects/construction/
```

### 4.4 Memory Isolation

```
/root/.openclaw/workspace/memory/
├── MEMORY.md                    ← Global/cross-project memory ONLY
├── projects/                    ← NEW: per-project memory
│   ├── psvibe/
│   │   ├── infrastructure.md
│   │   ├── project-state.md
│   │   ├── known-issues.md
│   │   └── contacts.md
│   ├── construction/
│   │   ├── infrastructure.md
│   │   ├── project-state.md
│   │   └── contacts.md
│   └── <new-project>/
│       └── ...
├── analysis/                    ← Cross-project analysis
├── sop/                         ← Global SOPs (project-agnostic)
└── archive/                     ← Archived memory
```

**Rule:** Cross-project info in root `memory/`. Project-specific info in `memory/projects/<slug>/`.

### 4.5 Database Isolation

| Isolation Level | When to Use | Example |
|----------------|------------|---------|
| **Separate MySQL container** | Totally independent projects | `construction-mysql` on port 3307 |
| **Separate database, shared container** | Related projects, same MySQL instance | `psvibe_api` + `psvibe_staging` on `psvibe-mysql` |
| **Same DB, branch_id column** | Multi-branch of same project | PS VIBE Sanchaung + PS VIBE Hledan |
| **Separate DB user** | Minimum isolation per project | Each project gets `CREATE USER '<project>_user'@'%'` with GRANT only on their DB |

**Current state:** PS VIBE uses shared MySQL container (`psvibe-mysql`) with single DB `psvibe_api`. For Project #2, use **separate DB user + separate database**, optionally separate container if performance isolation is needed.

---

## 5. Kora Orchestration Design

### 5.1 Project Registry (`/root/coordination/project_registry.json`)

```json
{
  "version": "1.0",
  "current_project": "psvibe",
  "projects": {
    "psvibe": {
      "name": "PS VIBE Gaming Lounge",
      "slug": "psvibe",
      "paths": {
        "bot": "/root/psvibe-sales-bot",
        "api": "/root/psvibe_api_server",
        "dashboard": "/root/psvibe-dashboard"
      },
      "services": [
        "psvibe-sale-bot",
        "psvibe-customer-bot",
        "psvibe-api",
        "psvibe-watchdog",
        "psvibe-analytics",
        "psvibe-attendance",
        "psvibe-discord-bot"
      ],
      "database": {
        "container": "psvibe-mysql",
        "name": "psvibe_api",
        "user": "psvibe_user"
      },
      "aliases": ["ps vibe", "psvibe", "ps5", "gaming lounge"],
      "memory_dir": "memory/projects/psvibe/"
    },
    "construction": {
      "name": "Three Brothers Construction Bot",
      "slug": "construction",
      "paths": {
        "bot": "/opt/construction-bot"
      },
      "services": [],
      "database": null,
      "aliases": ["construction", "three brothers", "ဆောက်လုပ်ရေး"],
      "memory_dir": "memory/projects/construction/"
    }
  }
}
```

### 5.2 Context Detection (`kora_context_switch.py`)

```python
#!/usr/bin/env python3
"""
Detect which project Boss is talking about.
Priority: explicit mention > current context > default (psvibe)
"""
import json, sys

def detect_project(message: str, registry_path="/root/coordination/project_registry.json"):
    with open(registry_path) as f:
        reg = json.load(f)
    
    msg_lower = message.lower()
    
    # 1. Explicit project mention
    for slug, proj in reg["projects"].items():
        if slug in msg_lower:
            return slug
        for alias in proj.get("aliases", []):
            if alias.lower() in msg_lower:
                return slug
    
    # 2. Current context (from active context file)
    try:
        with open("/tmp/kora_current_project.txt") as f:
            return f.read().strip()
    except:
        pass
    
    # 3. Default
    return reg.get("current_project", "psvibe")

if __name__ == "__main__":
    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    print(detect_project(msg))
```

### 5.3 Tool Standardization — The `--project` Flag

Every coordination tool MUST accept `--project <slug>`:

```python
# BEFORE (current - broken for multi-project):
python3 /root/coordination/validate.py

# AFTER (multi-project ready):
python3 /root/coordination/validate.py --project psvibe
python3 /root/coordination/validate.py --project construction
python3 /root/coordination/validate.py              # defaults to current context
```

All tools read from `project_registry.json` instead of hardcoding paths:

```python
# BEFORE:
BD = "/root/psvibe-sales-bot"
SERVICES = ["psvibe-sale-bot", "psvibe_customer_bot", "psvibe-api"]

# AFTER:
def load_project(slug):
    with open("/root/coordination/project_registry.json") as f:
        reg = json.load(f)
    return reg["projects"][slug]

proj = load_project(args.project)
BD = proj["paths"]["bot"]
SERVICES = proj["services"]
```

### 5.4 Context Switching in Kora's Runtime

When Boss mentions a project:
1. `kora_context_switch.py` detects the project
2. Kora writes current project to `/tmp/kora_current_project.txt`
3. Kora loads project-specific memory from `memory/projects/<slug>/`
4. All spawned sub-agents receive the project context in their task description
5. Sub-agents use `--project <slug>` when calling coordination tools

### 5.5 Task Routing

```
Boss: "ဆောက်လုပ်ရေး bot ကို deploy လုပ်ပါ"
  │
  ├─ kora_context_switch.py → "construction"
  ├─ Load: memory/projects/construction/*
  ├─ Spawn deploy sub-agent with: --project construction
  │   └─ deploy_manager.py reads construction config from registry
  │
Boss: "PS VIBE services တွေ restart လုပ်"
  │
  ├─ kora_context_switch.py → "psvibe" (alias match)
  ├─ Load: memory/projects/psvibe/*
  ├─ Spawn service sub-agent with: --project psvibe
  │   └─ auto_healer.py reads psvibe config from registry
```

---

## 6. Infrastructure Sharing

### 6.1 Shared (One Instance, All Projects)

| Component | How Shared | Notes |
|-----------|-----------|-------|
| **Docker Engine** | Single daemon, multiple containers | Every project can have its own containers |
| **Caddy Reverse Proxy** | Single instance, multiple vhosts | `ps-vibe.com`, `project2.com` |
| **Cloudflare Tunnel** | Single tunnel, multi-route | Route by hostname |
| **Fail2Ban** | Single instance | Protects SSH for all |
| **SSH** | Single instance | All projects on same VPS |
| **n8n** | Single instance (currently PS VIBE-only) | Can be shared with webhook routing |
| **Systemd** | Single init system | Each project has its own unit files |
| **MySQL Server** | Single `mysqld` process | Separate databases per project |
| **Kora/OpenClaw** | Single agent instance | Manages all projects |
| **Coordination tools** | Shared code, project-aware | `--project` flag routes to correct config |
| **Backup dir** | `/root/backups/` | Filename prefix isolates per project |

### 6.2 Isolated (Per-Project)

| Component | Isolation Strategy |
|-----------|-------------------|
| **Application Code** | Separate directories (`/root/<slug>/` or `/opt/<slug>/`) |
| **Systemd Services** | Per-project unit files (`<slug>-*`) |
| **Docker Containers** | Per-project containers with project prefix |
| **Database** | Separate databases (`<slug>_db`) in shared MySQL |
| **Database Users** | Separate users with `GRANT` only on own DB |
| **Environment Variables** | Separate `.env` or `/etc/<slug>/secrets.env` |
| **Git Repos** | Separate repos, separate remotes |
| **Memory/Knowledge** | Separate dirs under `memory/projects/<slug>/` |
| **Logs** | Separate log files or journald tags |
| **Backups** | Separate archive files with project prefix |

### 6.3 Decision Matrix: Share vs Isolate

```
                    ┌────────────────┬───────────────────┐
                    │   SHARE         │   ISOLATE         │
┌───────────────────┼────────────────┼───────────────────┤
│ VPS/Server        │ ✅ Same VPS     │                   │
│ Docker Engine     │ ✅ Shared       │                   │
│ MySQL             │ ✅ Shared       │ DB/user: isolate  │
│ Code              │                │ ✅ Separate dirs   │
│ Services          │                │ ✅ Separate units  │
│ Memory            │                │ ✅ Separate dirs   │
│ Git               │                │ ✅ Separate repos  │
│ Coordination      │ ✅ Same tools   │ --project flag    │
│ Caddy             │ ✅ Shared       │ Separate domains  │
│ SSH               │ ✅ Shared       │                   │
│ Fail2Ban          │ ✅ Shared       │                   │
│ Kora Agent        │ ✅ One Kora     │ Context switching │
└───────────────────┴────────────────┴───────────────────┘
```

---

## 7. Migration Plan

### Phase 1: Project Abstraction Layer (Week 1)

**Goal:** Create the foundation without breaking anything.

**Steps:**

1. **Create `project_registry.json`**
   ```bash
   cat > /root/coordination/project_registry.json << 'EOF'
   { ...see Section 5.1 above... }
   EOF
   ```

2. **Create `project_utils.py`** — shared library for all tools
   ```python
   # /root/coordination/project_utils.py
   import json, os
   
   REGISTRY = "/root/coordination/project_registry.json"
   
   def load_registry():
       with open(REGISTRY) as f:
           return json.load(f)
   
   def get_project(slug=None):
       reg = load_registry()
       if slug is None:
           slug = get_current_context()
       return reg["projects"].get(slug, reg["projects"]["psvibe"])
   
   def get_current_context():
       try:
           with open("/tmp/kora_current_project.txt") as f:
               return f.read().strip()
       except:
           return "psvibe"
   
   def add_project_arg(parser):
       parser.add_argument("--project", default=None,
           help="Project slug (default: current context)")
   ```

3. **Add `--project` flag to top 5 critical tools:**
   - `validate.py`
   - `preflight.py`
   - `auto_healer.py`
   - `deploy_manager.py`
   - `workflow_engine.py`

   Each tool should:
   ```python
   from project_utils import get_project, add_project_arg
   # ... in main():
   add_project_arg(parser)
   args = parser.parse_args()
   proj = get_project(args.project)
   # Use proj["paths"]["bot"] instead of hardcoded "/root/psvibe-sales-bot"
   ```

4. **Test:** Run all 5 tools with `--project psvibe` → must produce identical output to current no-flag behavior.

### Phase 2: Migrate PS VIBE to New Convention (Week 1-2)

**Goal:** PS VIBE becomes the first fully-compliant project under the new system.

**Steps:**

1. **Standardize PS VIBE service names** (requires downtime):
   ```bash
   # Rename with underscores → dashes
   # OLD: psvibe_customer_bot.service
   # NEW: psvibe-customer-bot.service
   
   systemctl stop psvibe_customer_bot.service
   mv /etc/systemd/system/psvibe_customer_bot.service \
      /etc/systemd/system/psvibe-customer-bot.service
   sed -i 's/psvibe_customer_bot/psvibe-customer-bot/g' \
      /etc/systemd/system/psvibe-customer-bot.service
   systemctl daemon-reload
   systemctl start psvibe-customer-bot.service
   ```

2. **Create per-project memory structure:**
   ```bash
   mkdir -p /root/.openclaw/workspace/memory/projects/psvibe
   # Move project-specific files:
   mv memory/infrastructure.md memory/projects/psvibe/
   mv memory/psvibe-code-structure.md memory/projects/psvibe/
   mv memory/project-state.md memory/projects/psvibe/
   ```

3. **Update all 43 hardcoded tools** to use `project_registry.json` + `--project` flag:
   - Batch 1 (critical): 15 tools that cause immediate breakage → update first
   - Batch 2 (tools with defaults only): 5 tools → update with `--project` flag, keep `psvibe` as default
   - Batch 3 (reporting tools): 8 tools → update
   - Batch 4 (remaining): 15 tools → update
   
   **Estimated effort:** ~5-10 lines changed per tool for basic flag support.

4. **Update Kora's AGENTS.md and SOUL.md:**
   - Add project context switching rules
   - Add `--project` flag documentation
   - Update memory fetching to check `memory/projects/<slug>/`

5. **Test full fix → verify → deploy loop on PS VIBE** using new project-aware tools.

### Phase 3: Onboard Existing Orphan Projects (Week 2-3)

**Goal:** Bring existing unmanaged projects under Kora's coordination.

**Eligible projects to onboard:**

| Project | Priority | Effort |
|---------|----------|--------|
| Construction Bot | 🔴 High (already in Docker, Boss uses it) | Low — add manifest, test |
| YYO Personal Wallet | 🟡 Medium | Low — already has systemd unit |
| ACM Personal Wallet | 🟡 Medium | Low — already has systemd unit |
| Social Auto Reply | 🟢 Low (tied to PS VIBE brand) | Low |
| Kora Voice | 🟢 Low (Kora's own voice) | Low |

**Steps per project:**

1. Create `PROJECT_MANIFEST.yaml` in project root
2. Add entry to `project_registry.json`
3. Create `memory/projects/<slug>/` with infrastructure.md + project-state.md
4. Test: `python3 /root/coordination/validate.py --project <slug>`
5. Test: `python3 /root/coordination/health_dashboard.py --project <slug>`
6. Test: `python3 /root/coordination/deploy_manager.py deploy --project <slug>`

### Phase 4: Add a New Project from Scratch (Week 3+)

**Goal:** Validate the entire system by onboarding a completely new project.

**Success criteria:**
- [ ] New project registered in < 5 minutes
- [ ] `validate.py --project <new>` passes on first run
- [ ] `deploy_manager.py deploy --project <new>` works
- [ ] `auto_healer.py` monitors new services
- [ ] `git_sync_agent.py` syncs new repo
- [ ] Kora correctly detects project context from Boss's messages
- [ ] Kora can spawn sub-agents that work on the new project
- [ ] Memory isolation works (new project doesn't see PS VIBE context)

---

## 8. Quick Wins — 3 Things Doable TODAY

### Quick Win #1: Create `project_registry.json`

```bash
python3 -c "
import json
registry = {
    'version': '1.0',
    'current_project': 'psvibe',
    'projects': {
        'psvibe': {
            'name': 'PS VIBE Gaming Lounge',
            'slug': 'psvibe',
            'paths': {
                'bot': '/root/psvibe-sales-bot',
                'api': '/root/psvibe_api_server',
                'dashboard': '/root/psvibe-dashboard'
            },
            'services': [
                'psvibe-sale-bot', 'psvibe_customer_bot', 'psvibe-api',
                'psvibe-watchdog', 'psvibe-analytics', 'psvibe-attendance',
                'psvibe-discord-bot', 'psvibe-social-autoreply'
            ],
            'database': {
                'container': 'psvibe-mysql',
                'name': 'psvibe_api',
                'user': 'psvibe_user'
            },
            'aliases': ['ps vibe', 'psvibe', 'ps5', 'gaming lounge',
                        'ps vibe gaming', 'ps5 lounge']
        }
    }
}
with open('/root/coordination/project_registry.json', 'w') as f:
    json.dump(registry, f, indent=2)
print('Created: /root/coordination/project_registry.json')
"
```

**Impact:** Establishes single source of truth. Zero risk to existing operations.

### Quick Win #2: Create `project_utils.py` Shared Library

```bash
cat > /root/coordination/project_utils.py << 'PYEOF'
#!/usr/bin/env python3
"""Shared project utilities for all coordination tools."""
import json, os, sys

REGISTRY_PATH = "/root/coordination/project_registry.json"
CONTEXT_FILE = "/tmp/kora_current_project.txt"

def load_registry():
    with open(REGISTRY_PATH) as f:
        return json.load(f)

def get_project(slug=None):
    reg = load_registry()
    if slug is None:
        slug = get_context()
    return reg["projects"].get(slug)

def get_context():
    try:
        with open(CONTEXT_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        return "psvibe"

def set_context(slug):
    with open(CONTEXT_FILE, 'w') as f:
        f.write(slug)

def add_project_arg(parser):
    parser.add_argument("--project", default=None,
        help=f"Project slug (default: current context or 'psvibe')")

def detect_project(message):
    reg = load_registry()
    msg_lower = message.lower() if message else ""
    for slug, proj in reg["projects"].items():
        if slug in msg_lower:
            return slug
        for alias in proj.get("aliases", []):
            if alias.lower() in msg_lower:
                return slug
    return get_context()
PYEOF
chmod +x /root/coordination/project_utils.py
echo "Created: /root/coordination/project_utils.py"
```

**Impact:** All future tools can `from project_utils import get_project, add_project_arg` instead of hardcoding paths.

### Quick Win #3: Patch `validate.py` to Support `--project`

```bash
# Add --project flag to validate.py (backward-compatible)
python3 << 'PYEOF'
import re

with open('/root/coordination/validate.py', 'r') as f:
    content = f.read()

# Add import
if 'from project_utils import' not in content:
    content = content.replace(
        '#!/usr/bin/env python3',
        '#!/usr/bin/env python3\nimport sys; sys.path.insert(0, "/root/coordination")\nfrom project_utils import get_project, add_project_arg',
        1
    )

# Add --project argument (find argparse section)
if 'add_project_arg' not in content:
    content = content.replace(
        'def main():',
        'def main():\n    parser = argparse.ArgumentParser()\n    add_project_arg(parser)\n    args = parser.parse_args()\n    proj = get_project(args.project)'
    )
    # Replace hardcoded BOT_DIR with dynamic
    content = re.sub(
        r"BOT_DIR = .*",
        'BOT_DIR = proj["paths"]["bot"]',
        content
    )
    # Replace hardcoded services with dynamic
    content = re.sub(
        r'SERVICES = \[.*?\]',
        'SERVICES = [(s, f"{s}.service") for s in proj.get("services", [])]',
        content, flags=re.DOTALL
    )

with open('/root/coordination/validate.py', 'w') as f:
    f.write(content)

print("Updated: /root/coordination/validate.py (added --project support)")
PYEOF
```

**Impact:** First tool becomes multi-project aware. Same pattern can be replicated across all 43 tools.

---

## 9. Risk Assessment

### 🔴 High Risk

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Tool breakage during migration** — Changing 43 tools simultaneously | Medium | 🔴 Critical | Phase-by-phase rollout; keep PS VIBE as default; test with `--project psvibe` first |
| **Service rename causes downtime** — Renaming `psvibe_customer_bot` → `psvibe-customer-bot` | Medium | 🔴 Critical | Do during maintenance window; keep symlink for backward compat |
| **Database user confusion** — Wrong credentials used for wrong project | Low | 🔴 Critical | `project_registry.json` is single source of truth; never hardcode creds |
| **Sub-agent works on wrong project** — Kora spawns agent that modifies wrong codebase | Medium | 🔴 Critical | Task description always includes explicit `--project <slug>` and `PROJECT_DIR=...` |

### 🟡 Medium Risk

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Context detection fails** — Boss uses ambiguous terms, wrong project detected | Medium | 🟡 High | Require explicit "PS VIBE" or project name mention; default to PS VIBE (least surprise) |
| **Memory leak between projects** — PS VIBE memory accidentally loaded for construction project | Low | 🟡 Medium | Memory file isolation by directory; strict prefix rules |
| **Registry drift** — `project_registry.json` becomes outdated vs actual deployed state | Medium | 🟡 Medium | Auto-validate registry against actual state; add registry check to heartbeat |
| **Performance contention** — Multiple projects on single VPS strain resources | Low | 🟡 Medium | Monitor resource usage per project; plan for VPS upgrade if needed |

### 🟢 Low Risk

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **n8n webhook collision** — Same webhook path across projects | Low | 🟢 Low | Route by hostname (Caddy) or prefix |
| **Docker port conflict** — Two MySQL containers both want 3306 | Low | 🟢 Low | Assign unique ports; document in registry |
| **Git conflict** — Two projects share same repo name | Very Low | 🟢 Low | GitHub org/repo separation prevents this |

---

## 10. Summary: The Critical Numbers

| Metric | Current | Target |
|--------|---------|--------|
| Coordination tools | 52 | 52 (all project-aware) |
| Tools with hardcoded psvibe paths | 43 (83%) | 0 |
| Total hardcoded psvibe references | 174 | 0 |
| Unmanaged orphan projects | 5 | 0 |
| Project detection mechanism | None | `project_registry.json` + context switch |
| Memory isolation | None | `memory/projects/<slug>/` |
| Service name convention | Inconsistent (dashes + underscores) | Consistent (dashes only) |
| Database isolation | Single DB `psvibe_api` | Per-project DBs with separate users |
| Current multi-project readiness | **17%** (9/52 tools safe) | **100%** |

---

## 11. What NOT to Do

1. ❌ **Don't create a new VPS for Project #2** — Kora is designed to orchestrate multiple projects on the same host; adding a VPS fragments management.
2. ❌ **Don't fork the coordination tools** — Creating `coordination-psvibe/` and `coordination-project2/` is a maintenance nightmare. One codebase with `--project`.
3. ❌ **Don't rename services without backward compatibility** — Keep old symlinks or `Alias=` for 30 days after rename.
4. ❌ **Don't onboard all 5 orphan projects at once** — Phase 3 should be 1 project → test → next project.
5. ❌ **Don't delete PS VIBE hardcoded paths** — Add `--project` support first, keep defaults, then deprecate.

---

_Generated by Kora Sub-Agent (DeepSeek Pro) | 2026-06-25 02:15 UTC_

=== RESULT: OK ||| ERROR: ===
