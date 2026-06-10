#!/usr/bin/env python3
"""Fix 2 remaining bare excepts in bot/__init__.py"""

with open("/root/psvibe-sales-bot/bot/__init__.py") as f:
    content = f.read()

# Fix 1: Line 1758 - date parse in _filter_valid_promos
old1 = """                    except: pass
                # Filter out null/empty titles (fix 2026-06-04)"""
new1 = """                    except (ValueError, AttributeError): pass
                # Filter out null/empty titles (fix 2026-06-04)"""
content = content.replace(old1, new1)

# Fix 2: Line 1791 - date parse in _refresh_promo_cache
old2 = """            except: pass
        _f.append(_p)"""
new2 = """            except (ValueError, AttributeError): pass
        _f.append(_p)"""
content = content.replace(old2, new2)

with open("/root/psvibe-sales-bot/bot/__init__.py", "w") as f:
    f.write(content)

# Verify
import subprocess, os
r = subprocess.run(
    'cd /root/psvibe-sales-bot && grep -rn "^\\s*except:" bot/__init__.py 2>/dev/null | wc -l',
    shell=True, capture_output=True, text=True
)
count = r.stdout.strip()
print(f"Remaining bare excepts in __init__.py: {count}")

os.system("python3 -m py_compile /root/psvibe-sales-bot/bot/__init__.py 2>&1 && echo 'COMPILE OK'")
