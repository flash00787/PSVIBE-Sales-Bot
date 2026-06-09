# AUDIT REPORT TEMPLATE v2.1
## Standard format — ကျစ်လျစ် + ရှင်းပြချက်ပါ

---

## 📋 Report: [Report Name]
**Date:** YYYY-MM-DD HH:MM UTC | **Auditor:** [agent-name] | **Files scanned:** N

---

## 🔴 CRITICAL (N issues)
| # | File:Line | Before | After | Why? |
|---|-----------|--------|-------|------|
| 1 | `bot/__init__.py:1288` | `WL_MENU, PAY_METHOD, PAY_AMOUNT = BotState.WL_MENU, PAY_METHOD, PAY_AMOUNT` (tuple unpack int) | `WL_MENU = BotState.WL_MENU` etc (separate lines) | Parallel sub-agent rewrote alias lines → Python `cannot unpack non-iterable int` crash |

## 🟡 HIGH (N issues)
| # | File:Line | Before | After | Why? |
|---|-----------|--------|-------|------|
| 1 | `customer_bot/api.py:15` | `headers={"X-API-Key": key}` | `params={"api_key": key}` | API server reads key from query params, not headers → 401 crash |

## 🟢 MEDIUM (N issues)
| # | File:Line | Before | After | Why? |
|---|-----------|--------|-------|------|
| 1 | `referral.py:99` | `row[13]` (reserved col) | `row[16]` (referral col) | Sheet schema shifted; wrong col → empty check returned True for all users |

## ⚪ LOW (N issues)
| # | File:Line | Issue | Why? |
|---|-----------|-------|------|
| 1 | `notify.py:1` | Docstring had fake `from bot import *` | Copy-paste from another file |

---

## ✅ CLEAN (Verified — No issues)
- `bot/handlers/sales.py` — 18 states, all handlers registered
- `bot/app.py` — State machine registration OK
- `bot/api_client.py` — All API paths match backend

---

## 📊 Summary
| Severity | Count | Fixed | Pending |
|----------|-------|-------|---------|
| 🔴 Critical | 3 | 3 | 0 |
| 🟡 High | 5 | 5 | 0 |
| 🟢 Medium | 2 | 2 | 0 |
| ⚪ Low | 1 | 1 | 0 |
| **Total** | **11** | **11** | **0** |

**Service Status:** ✅ All 3 services active
**Compile:** ✅ PASS (50 files)
**Imports:** ✅ OK

---

## Files Modified
- `bot/__init__.py` — 3 BotState values, 1 function
- `customer_bot/api.py` — Auth method
- `referral.py` — Column index

---

## Notes
- **Root cause:** Parallel sub-agents (6) editing `bot/__init__.py` simultaneously without locks → chain-reaction corruption. See Framework v2.0 for prevention.
- **Fix approach:** Sequential fixes with coordination framework after deploying lock_manager, preflight, validate, rollback.
