with open('/root/psvibe-sales-bot/bot/__init__.py', 'r') as f:
    content = f.read()

old1 = '                    except: pass\n                _f.append(_p)'
new1 = '                    except: pass\n                # Filter out null/empty titles (fix 2026-06-04)\n                if not _p.get("title", "").strip():\n                    continue\n                # Filter out test entries (fix 2026-06-04)\n                if "Test" in _p.get("title", "") or "TEST" in _p.get("title", "").upper():\n                    continue\n                # Filter out empty discount_type (fix 2026-06-04)\n                if not _p.get("type", "").strip():\n                    continue\n                _f.append(_p)'
content = content.replace(old1, new1, 1)

with open('/root/psvibe-sales-bot/bot/__init__.py', 'w') as f:
    f.write(content)
print('FIX 2 API filter applied')
