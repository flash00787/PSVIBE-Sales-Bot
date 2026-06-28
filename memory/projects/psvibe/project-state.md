# PS VIBE — Project State

## Status: Active ✅
**Last updated:** 2026-06-28 02:05 UTC

## Current Features
- Full booking system (Staff + Customer Bot)
- Console management with timer tracking
- Food cart ordering system (Phase 1 complete, Phase 2 pending: Customer Bot self-order)
- Staff salary system with auto-generated payroll (leave tracking, food commission, game bonus)
- PNL & Balance Sheet financial reporting
- 35-command Discord bot with auto-mod, LFG, suggestions
- Vue web dashboard (10+ pages: Timeline, Console Timers, Food Orders, Sale Daily, Staff, Finance, Feedback)
- Member wallet system (MySQL-backed)

## Known Issues
| Issue | Status |
|-------|--------|
| Cashflow month filter not applied | 🔴 Pending |
| Cashflow asset deduction double-count | 🔴 Pending |
| VPS health monitor unreachable | 🟡 Investigating |

## Next Up
- Fix cashflow bugs (awaiting Boss confirmation)
- Customer Bot food self-ordering (Phase 2)
- Multi-branch support (Phase 2 audit complete, implementation pending)

## Infrastructure
- API: `/root/psvibe_api_server/` (FastAPI, port 8000)
- Dashboard: `/root/psvibe-dashboard/` (Vue 3 + Vite)
- Sale Bot: `/root/psvibe-sales-bot/`
- Server: `5.223.81.16` (VPS)
