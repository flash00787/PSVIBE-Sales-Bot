#!/usr/bin/env python3
"""Fix remaining bare excepts and print() statements in production code.
Targets: bot/*.py and customer_bot/*.py (scanned by quality gate)"""

import re, os

SALES = "/root/psvibe-sales-bot"

def fix_file(path, old_text, new_text, desc):
    with open(path) as f:
        content = f.read()
    if old_text not in content:
        print(f"  SKIP {desc}: text not found in {path}")
        return False
    content = content.replace(old_text, new_text)
    with open(path, "w") as f:
        f.write(content)
    print(f"  FIXED {desc}")
    return True

# === FIX 1: bot/__init__.py bare excepts (date parsing) ===
fix_file(
    f"{SALES}/bot/__init__.py",
    "                        except: pass\n                # Filter out null/empty titles",
    "                        except (ValueError, AttributeError): pass\n                # Filter out null/empty titles",
    "__init__.py bare except 1 (line 1758)"
)

fix_file(
    f"{SALES}/bot/__init__.py",
    "                except: pass\n        _f.append(_p)",
    "                except (ValueError, AttributeError): pass\n        _f.append(_p)",
    "__init__.py bare except 2 (line 1791)"
)

# === FIX 2: bot/handlers/main_menu.py bare excepts ===
# Fix 1: except: pass after import attempt
fix_file(
    f"{SALES}/bot/handlers/main_menu.py",
    "    except:\n        pass\n    \n    if user_id not in allowed:",
    "    except (ImportError, AttributeError):\n        pass\n    \n    if user_id not in allowed:",
    "main_menu.py bare except 1 (line 104)"
)

# Fix 2: except: after amount parse
fix_file(
    f"{SALES}/bot/handlers/main_menu.py",
    "    try:\n        amount = int(context.args[0].replace(\",\", \"\"))\n    except:\n        await update.message.reply_text",
    "    try:\n        amount = int(context.args[0].replace(\",\", \"\"))\n    except (ValueError, TypeError):\n        await update.message.reply_text",
    "main_menu.py bare except 2 (line 121)"
)

# === FIX 3: customer_bot/booking_handlers.py bare except ===
fix_file(
    f"{SALES}/customer_bot/booking_handlers.py",
    "        except:\n            pass\n    available = []",
    "        except (ValueError, AttributeError):\n            pass\n    available = []",
    "booking_handlers.py bare except (line 245)"
)

# === FIX 4: bot/handlers/notify.py print() ===
fix_file(
    f"{SALES}/bot/handlers/notify.py",
    '        print(f"Failed to send coupon notification: {e}")',
    '        logging.error(f"Failed to send coupon notification: {e}")',
    "notify.py print() statement"
)

# === FIX 5: customer_bot/fix_unicode.py print() ===
with open(f"{SALES}/customer_bot/fix_unicode.py") as f:
    content = f.read()

old = 'print("Script loaded")\nprint(f"Old bytes: {old}")'
new = 'logging.info("Script loaded")\nlogging.info(f"Old bytes: {old}")'

if old in content:
    # Also need to add logging import
    if "import logging" not in content:
        content = content.replace(old, new)
        content = "import logging\nlogging.basicConfig(level=logging.DEBUG)\n" + content
        print("  FIXED fix_unicode.py: added logging import + replaced prints")
    else:
        content = content.replace(old, new)
        print("  FIXED fix_unicode.py: replaced prints with logging.info")
    with open(f"{SALES}/customer_bot/fix_unicode.py", "w") as f:
        f.write(content)
else:
    # Try individual replacements
    for orig, repl, d in [
        ('print("Script loaded")', 'logging.info("Script loaded")', "fix_unicode.py print 1"),
        ('print(f"Old bytes: {old}")', 'logging.info(f"Old bytes: {old}")', "fix_unicode.py print 2"),
    ]:
        fix_file(f"{SALES}/customer_bot/fix_unicode.py", orig, repl, d)

# === Verify all compiles ===
print("\n=== Verification ===")
for p in [
    "bot/__init__.py",
    "bot/handlers/main_menu.py",
    "customer_bot/booking_handlers.py",
    "bot/handlers/notify.py",
    "customer_bot/fix_unicode.py",
]:
    path = f"{SALES}/{p}"
    r = os.system(f"python3 -m py_compile {path} 2>&1")
    status = "COMPILE OK" if r == 0 else "COMPILE FAIL"
    print(f"  {p}: {status}")

# === Final counts ===
import subprocess
for scan_dir, label in [("bot", "bot"), ("customer_bot", "customer_bot")]:
    r = subprocess.run(
        f'cd {SALES} && grep -rn "^\\\\s*print(" {scan_dir}/*.py 2>/dev/null | grep -v __pycache__ | wc -l',
        shell=True, capture_output=True, text=True
    )
    count = r.stdout.strip()
    print(f"  Print() in {label}/*.py: {count}")

    r = subprocess.run(
        f'cd {SALES} && grep -rn "^\\\\s*except:" {scan_dir}/*.py 2>/dev/null | grep -v __pycache__ | wc -l',
        shell=True, capture_output=True, text=True
    )
    count = r.stdout.strip()
    print(f"  Bare except: in {label}/*.py: {count}")

print("\nDone.")
