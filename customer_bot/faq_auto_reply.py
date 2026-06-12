"""
PS VIBE FAQ Auto-Reply Module — bridges Kora FAQ with Customer Bot
Loads from customer_bot/psvibe_faq.json
"""
import json, os, re, logging, random
from typing import Optional

_log = logging.getLogger(__name__)

_FAQ_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "psvibe_faq.json")
_compiled = None
_fallbacks = None

def load():
    global _compiled, _fallbacks
    if _compiled is not None:
        return True
    if not os.path.exists(_FAQ_PATH):
        _log.warning("FAQ not found at %s", _FAQ_PATH)
        return False
    try:
        with open(_FAQ_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        _log.warning("FAQ parse error: %s", e)
        return False
    _compiled = []
    greeting = data.get("greeting_keywords", {})
    g_kw = [k.lower().strip() for k in greeting.get("keywords", [])]
    g_resp = greeting.get("response", "")
    if g_kw and g_resp:
        _compiled.append(("_greeting", g_kw, g_kw, g_resp))
    for cat_key, cat in data.get("categories", {}).items():
        for item in cat.get("items", []):
            kw = [k.lower().strip() for k in item.get("keywords", [])]
            pt = [p.lower().strip() for p in item.get("patterns", [])]
            _compiled.append((item.get("id",""), kw, pt, item.get("answer","")))
    _fallbacks = data.get("fallback_answers", [])
    _log.info("FAQ loaded: %d patterns from %s", len(_compiled), _FAQ_PATH)
    return True

def match_faq(text: str) -> Optional[str]:
    if not load() or not text:
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
    if best and best_score >= 1 and _fallbacks:
        return random.choice(_fallbacks) if _fallbacks else None
    return None

def test():
    print(load())
    for q in ["price", "ဘယ်လောက်လဲ", "ဘယ်အချိန်ဖွင့်လဲ", "မင်္ဂလာပါ", "ဘယ်မှာလဲ", "ဘယ်ဂိမ်းတွေရှိလဲ"]:
        print(f"  {q}: {match_faq(q)[:50] if match_faq(q) else None}")

if __name__ == "__main__":
    test()
