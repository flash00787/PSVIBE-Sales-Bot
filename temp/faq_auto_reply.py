"""
PS VIBE FAQ Auto-Reply Module — bridges Kora FAQ with Customer Bot
Inserts FAQ check before menu button routing in handle_menu_buttons()
"""
import json, os, re, logging
from typing import Optional

_log = logging.getLogger(__name__)

# Load FAQ from Kora workspace (relative path)
FAQ_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "knowledge", "psvibe_faq.json")

_faq_data = None
_compiled_patterns = []

def _load_faq():
    global _faq_data, _compiled_patterns
    if _faq_data is not None:
        return _faq_data
    
    # Try multiple locations
    for path in [
        FAQ_PATH,
        "/home/node/.openclaw/workspace/knowledge/psvibe_faq.json",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "home", "node", ".openclaw", "workspace", "knowledge", "psvibe_faq.json"),
    ]:
        path = os.path.abspath(path)
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    _faq_data = json.load(f)
                _log.info("FAQ loaded from %s", path)
                break
            except Exception as e:
                _log.warning("Failed to load FAQ from %s: %s", path, e)
    
    if _faq_data is None:
        _log.warning("FAQ file not found — auto-reply disabled")
        return None
    
    # Pre-compile keyword patterns
    _compiled_patterns = []
    for cat_key, cat in _faq_data.get("categories", {}).items():
        for item in cat.get("items", []):
            keywords = [k.lower().strip() for k in item.get("keywords", [])]
            patterns = [p.lower().strip() for p in item.get("patterns", [])]
            _compiled_patterns.append({
                "id": item.get("id", ""),
                "category": cat.get("label", ""),
                "keywords": keywords,
                "patterns": patterns,
                "answer": item.get("answer", ""),
            })
    
    # Greeting
    greeting = _faq_data.get("greeting_keywords", {})
    _greeting_keywords = [k.lower().strip() for k in greeting.get("keywords", [])]
    _greeting_response = greeting.get("response", "")
    if _greeting_keywords and _greeting_response:
        _compiled_patterns.insert(0, {
            "id": "_greeting",
            "category": "👋 Greeting",
            "keywords": _greeting_keywords,
            "patterns": _greeting_keywords,
            "answer": _greeting_response,
        })
    
    _log.info("FAQ compiled: %d patterns loaded", len(_compiled_patterns))
    return _faq_data

def match_faq(text: str) -> Optional[str]:
    """Check text against FAQ keywords. Returns answer if matched, None otherwise."""
    data = _load_faq()
    if data is None or not text:
        return None
    
    text_lower = text.lower().strip()
    
    # Score-based matching
    best_match = None
    best_score = 0
    
    for entry in _compiled_patterns:
        score = 0
        # Check patterns (exact/fuzzy)
        for pattern in entry.get("patterns", []):
            if pattern in text_lower or text_lower in pattern:
                score += 3
                break
        
        # Check keywords
        for keyword in entry.get("keywords", []):
            if keyword in text_lower:
                score += 1
        
        if score > best_score:
            best_score = score
            best_match = entry
    
    # Threshold: score must be >= 2 (at least one pattern match or 2 keyword matches)
    if best_match and best_score >= 2:
        # For greeting, require higher confidence
        if best_match["id"] == "_greeting" and best_score < 2:
            return None
        return best_match["answer"]
    
    # Fallback — check if any fallback answer is appropriate (low confidence)
    if best_match and best_score == 1:
        fallbacks = data.get("fallback_answers", [])
        if fallbacks:
            import random
            return random.choice(fallbacks)
    
    return None
