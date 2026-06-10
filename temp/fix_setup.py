#!/usr/bin/env python3
"""Fix 3 bare except: clauses in sqlite/setup.py"""

with open("/root/psvibe-sales-bot/sqlite/setup.py") as f:
    content = f.read()

# Fix 1: _int_safe bare except (around line 286)
old = """            def _int_safe(s):
                try: return int(str(s).strip())
                except: return 0"""
new = """            def _int_safe(s):
                try: return int(str(s).strip())
                except (ValueError, TypeError): return 0"""
content = content.replace(old, new)

# Fix 2: Staff salary parse bare except (around line 315)
old = """            except:
                sal_num = 0"""
new = """            except (ValueError, TypeError):
                sal_num = 0"""
content = content.replace(old, new)

# Fix 3: _num bare except (around line 335)
old = """                except: return 0.0"""
new = """                except (ValueError, TypeError): return 0.0"""
content = content.replace(old, new)

with open("/root/psvibe-sales-bot/sqlite/setup.py", "w") as f:
    f.write(content)

# Verify
remaining = 0
for i, line in enumerate(content.split("\n"), 1):
    stripped = line.strip()
    if stripped == "except:" or (stripped.startswith("except:") and not "except:" in stripped[7:]):
        remaining += 1
        print(f"  STILL BARE: line {i}: {stripped[:60]}")

if remaining == 0:
    print("PASS: All 3 bare excepts fixed in setup.py")
else:
    print(f"WARN: {remaining} bare except(s) remain")
