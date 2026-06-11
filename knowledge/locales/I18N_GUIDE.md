# 🌐 Multi-Language Integration Guide

## How to add i18n to any PS VIBE bot

### 1. Import
```python
import json
import re

# Load translations
with open('/root/psvibe-sales-bot/knowledge/locales/bot_strings.json') as f:
    I18N = json.load(f)

def detect_lang(text):
    """Detect Myanmar or English"""
    return 'mm' if re.search(r'[\u1000-\u109F]', text) else 'en'

def t(key, lang='mm'):
    """Translate key to target language"""
    return I18N.get(key, {}).get(lang, key)
```

### 2. Usage in handlers
```python
# Auto-detect language from user message
lang = detect_lang(user_message)

# Simple translation
reply = t('welcome', lang)

# With formatting
reply = f"{t('total_amount', lang)}: 5,000 Ks"
```

### 3. Template strings
```python
def t_format(template, **vars):
    """Template with {variable} substitution"""
    text = I18N.get(template, {}).get(lang, template)
    for k, v in vars.items():
        text = text.replace(f'{{{k}}}', str(v))
    return text

# Example:
# t_format('balance_info', member='PSV_A001', balance='50,000')
```

### Locale files:
- `knowledge/locales/en.json` — English strings
- `knowledge/locales/mm.json` — Myanmar strings
- `knowledge/locales/bot_strings.json` — Combined for bot import

### To add new translations:
1. Edit `knowledge/i18n.js` → add entry to TRANSLATIONS
2. Run: `node knowledge/i18n.js export`
3. Run: `node knowledge/i18n.js bot`
