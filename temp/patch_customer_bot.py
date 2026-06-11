#!/usr/bin/env python3
"""Patch customer bot handlers.py to add Kora FAQ auto-reply support."""
import os

HANDLERS_PATH = "/root/psvibe-sales-bot/customer_bot/handlers.py"
FAQ_MODULE_PATH = "/root/psvibe-sales-bot/customer_bot/faq_auto_reply.py"

# 1. Create FAQ module if not exists
faq_module = '''"""
PS VIBE FAQ Auto-Reply Module — bridges Kora FAQ with Customer Bot
"""
import json, os, re, logging, random
from typing import Optional

_log = logging.getLogger(__name__)

# Kora FAQ path (workspace mounted at /root/psvibe-sales-bot/../ or home/node)
_FAQ_CANDIDATES = [
    "/root/psvibe-sales-bot/../knowledge/psvibe_faq.json",
    "/home/node/.openclaw/workspace/knowledge/psvibe_faq.json",
    "/root/psvibe-sales-bot/knowledge/psvibe_faq.json",
]

_compiled = None

def _load():
    global _compiled
    if _compiled is not None:
        return True
    for path in _FAQ_CANDIDATES:
        p = os.path.abspath(path)
        if os.path.exists(p):
            try:
                with open(p, encoding="utf-8") as f:
                    data = json.load(f)
                _compiled = []
                greeting = data.get("greeting_keywords", {})
                g_keywords = [k.lower().strip() for k in greeting.get("keywords", [])]
                g_response = greeting.get("response", "")
                if g_keywords and g_response:
                    _compiled.append(("_greeting", g_keywords, g_keywords, g_response))
                for cat_key, cat in data.get("categories", {}).items():
                    for item in cat.get("items", []):
                        kw = [k.lower().strip() for k in item.get("keywords", [])]
                        pt = [p.lower().strip() for p in item.get("patterns", [])]
                        _compiled.append((item.get("id",""), kw, pt, item.get("answer","")))
                _fallbacks = data.get("fallback_answers", [])
                _log.info("FAQ loaded: %d patterns from %s", len(_compiled), p)
                return True
            except Exception as e:
                _log.warning("FAQ load error: %s", e)
    _log.warning("FAQ file not found at any candidate path")
    return False

def match_faq(text: str) -> Optional[str]:
    """Check text against FAQ. Returns answer string or None."""
    if not _load() or not text:
        return None
    tl = text.lower().strip()
    best, best_score = None, 0
    for eid, keywords, patterns, answer in _compiled:
        score = 0
        for p in patterns:
            if p in tl or tl in p:
                score += 3
                break
        for kw in keywords:
            if kw in tl:
                score += 1
        if score > best_score:
            best_score, best = score, answer
    if best and best_score >= 2:
        return best
    if best and best_score == 1:
        fallbacks = ["ကျေးဇူးပြုပြီး Customer Bot မှာ /start လုပ်ပြီး အသေးစိတ်မေးမြန်းနိုင်ပါတယ်။"]
        return random.choice(fallbacks) if fallbacks else None
    return None
'''

# 2. Write FAQ module
with open(FAQ_MODULE_PATH, "w", encoding="utf-8") as f:
    f.write(faq_module)
print("✅ FAQ module written")

# 3. Read handlers.py
with open(HANDLERS_PATH, encoding="utf-8") as f:
    content = f.read()

# 4. Add import if not already present
if "faq_auto_reply" not in content:
    # Find a good insertion point — after last import from .ai
    marker = "from .ai import _ai_reply, _detect_ai_bypass, _build_faq_template"
    new_import = "from .faq_auto_reply import match_faq as _match_faq"
    if marker in content:
        content = content.replace(marker, marker + "\n" + new_import)
        print("✅ Import added")
    else:
        # Fallback: find the import block end
        lines = content.split("\n")
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("from .") or line.startswith("import "):
                insert_at = i + 1
        if insert_at > 0:
            lines.insert(insert_at, new_import)
            content = "\n".join(lines)
            print("✅ Import added (fallback)")
        else:
            print("❌ Could not find import insertion point")

# 5. Add FAQ check in handle_menu_buttons
faq_check_code = '''    # ⚡ Kora FAQ Auto-Reply
    faq_answer = _match_faq(text)
    if faq_answer:
        await update.message.reply_text(faq_answer, parse_mode="HTML")
        return

'''

# Find async def handle_menu_buttons
hkb_marker = "async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):"
if hkb_marker in content:
    # Insert FAQ check after the function signature line (first line of body = next line has text = ...)
    idx = content.index(hkb_marker)
    # Find the first actual statement after the def line
    lines = content.split("\n")
    def_line_idx = None
    for i, line in enumerate(lines):
        if hkb_marker in line:
            def_line_idx = i
            break
    
    if def_line_idx is not None:
        body_start = def_line_idx + 1
        # Skip blank/comment lines
        while body_start < len(lines) and (not lines[body_start].strip() or lines[body_start].strip().startswith("#")):
            body_start += 1
        # Insert FAQ check before the first statement (text = ...)
        lines.insert(body_start, faq_check_code)
        content = "\n".join(lines)
        print("✅ FAQ check inserted in handle_menu_buttons")
    else:
        print("❌ Could not find function definition")
else:
    print("❌ Could not find handle_menu_buttons function")

# 6. Write back
with open(HANDLERS_PATH, "w", encoding="utf-8") as f:
    f.write(content)

# 7. Verify syntax
import ast
try:
    ast.parse(open(HANDLERS_PATH).read())
    print("✅ Syntax verified — no errors")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")

# 8. Check the result
print("\n🔍 Line 24-28 (import area):")
os.system(f"sed -n '24,28p' {HANDLERS_PATH}")
print("\n🔍 Line 790-800 (FAQ check area):")
os.system(f"sed -n '790,800p' {HANDLERS_PATH}")
