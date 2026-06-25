# 📐 Kora Multi-Project Conventions

> Established: 2026-06-25  
> Purpose: Standardize all projects under Kora's management  

---

## Directory Structure (Going Forward)

All NEW projects use this standard layout:

```
/opt/kora-projects/<slug>/
├── PROJECT_MANIFEST.yaml     ← REQUIRED: project metadata
├── code/                     ← your source code
│   ├── .git/
│   ├── main.py / bot.js      ← entry point
│   └── ...
├── config/                   ← configuration files
│   ├── secrets.env
│   └── ...
├── docker-compose.yml        ← if Docker-based
└── Dockerfile
```

**Onboarding:** `python3 /root/coordination/onboard_project.py <slug> <name> <path>`

---

## Naming Rules

| Element | Convention | Example |
|---------|-----------|---------|
| **Project slug** | lowercase, dashes only | `my-new-bot` |
| **Systemd unit** | `<slug>-<component>.service` | `my-bot.service` |
| **Docker container** | `<slug>_<component>` | `my_bot_mysql` |
| **Database name** | `<slug>_db` | `my_bot_db` |
| **Database user** | `<slug>_user` | `my_bot_user` |
| **Backup file** | `<slug>_backup_<timestamp>.tar.gz` | `my_bot_backup_20260625.tar.gz` |
| **GitHub repo** | `flash00787/<slug>` | `flash00787/my-bot` |
| **Memory dir** | `memory/projects/<slug>/` | `memory/projects/my_bot/` |

---

## Service Naming

```
✅ CORRECT:
   psvibe-customer-bot.service   (dashes)
   construction-bot              (dashes)
   my-new-bot.service            (dashes)

❌ WRONG:
   psvibe_customer_bot.service   (underscores — legacy, being phased out)
   MyBot.service                 (CamelCase)
   my bot.service                (spaces)
```

---

## Project Types

| Type | Language | Typical Structure |
|------|----------|-------------------|
| `telegram-bot` | python | `main.py`, `bot/`, `handlers/` |
| `telegram-bot` | nodejs | `bot.js`, `node_modules/` |
| `web-app` | python | FastAPI/Django, `app.py`, `routes/` |
| `api` | python | `app.py`, `routes/`, `models/` |
| `discord-bot` | nodejs | `bot.js`, `commands/` |
| `automation` | mixed | `cron/`, `scripts/` |

---

## Onboarding Checklist

- [ ] `PROJECT_MANIFEST.yaml` in project root
- [ ] Entry in `project_registry.json`
- [ ] `memory/projects/<slug>/` with `infrastructure.md` + `project-state.md`
- [ ] `onboard_project.py <slug> <name> <path>` run
- [ ] `validate.py --project <slug> --quick` passes
- [ ] `kora_status.py` shows project with 🟢
- [ ] Aliases configured for auto-detection
- [ ] Backup globs configured
