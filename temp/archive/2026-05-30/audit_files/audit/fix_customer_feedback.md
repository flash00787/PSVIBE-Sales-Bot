# CB-6: Fix Customer Bot Feedback Callback

**Date:** 2026-05-28  
**File:** `psvibe_customer_src/customer_bot/main.py`  
**Status:** Fix identified, needs root to apply

## Root Cause

The feedback callback query handlers `cb_feedback_comment_prompt` and `cb_feedback_skip` are **defined** in `handlers.py` (lines 667, 685) but were **never registered** in `_register_handlers()` in `main.py`.

This means when a user clicks the "💬 Comment" or "✅ OK" buttons after rating, the Telegram callback query is silently ignored — no handler matches the callback_data.

## Actual Callback Data (from handlers.py)

| Button | `callback_data` | Handler |
|---|---|---|
| 💬 Comment ထည့်မည် | `fbc:{rating}:{bk_id}` (line 658) | `cb_feedback_comment_prompt` (line 667) |
| ✅ OK ပြီပြီ | `fbskip` (line 659) | `cb_feedback_skip` (line 685) |

## Fix Applied

Added two `CallbackQueryHandler` registrations after `cb_wl_action`:

```diff
     app.add_handler(CallbackQueryHandler(orig.cb_wl_action, pattern=r'^wl:(check|cancel:\d+)$'))
+    app.add_handler(CallbackQueryHandler(orig.cb_feedback_comment_prompt, pattern=r'^fbc:'))
+    app.add_handler(CallbackQueryHandler(orig.cb_feedback_skip, pattern=r'^fbskip$'))
     app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, orig.handle_menu_buttons))
```

| Pattern | Matches |
|---|---|
| `^fbc:` | `fbc:1:123`, `fbc:3:456`, etc. |
| `^fbskip$` | exact `fbskip` |

The comment text flow already works: `handle_menu_buttons` checks `_fb_waiting_comment` (set by `cb_feedback_comment_prompt`) and routes to the feedback submit logic.

## ⚠️  To Apply

The file is root-owned. Apply with root:

```bash
cp /home/node/.openclaw/workspace/audit/fix_customer_feedback.patch /tmp/
cd /home/node/.openclaw/workspace/psvibe_customer_src/customer_bot/
patch < /home/node/.openclaw/workspace/audit/fix_customer_feedback.patch
# OR manually add the 2 lines after line 66 (cb_wl_action)
```

Then restart the customer bot.
