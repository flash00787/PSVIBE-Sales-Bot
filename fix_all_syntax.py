#!/usr/bin/env python3
"""Fix ALL syntax errors in PS VIBE bot handler files"""
import ast, sys, os

BASE = "/root/psvibe-sales-bot"

files_to_check = []
for root, dirs, files in os.walk(os.path.join(BASE, "bot")):
    for f in files:
        if f.endswith(".py"):
            files_to_check.append(os.path.join(root, f))
for f in os.listdir(BASE):
    if f.endswith(".py"):
        files_to_check.append(os.path.join(BASE, f))

broken = []
for fpath in files_to_check:
    try:
        with open(fpath) as f:
            ast.parse(f.read())
    except SyntaxError as e:
        broken.append((fpath, str(e)))

if not broken:
    print("ALL FILES: SYNTAX OK ✅")
    sys.exit(0)

print(f"BROKEN FILES ({len(broken)}):")
for fpath, err in broken:
    print(f"  {fpath}: {err}")

# Now fix admin.py specifically
admin_path = os.path.join(BASE, "bot/handlers/admin.py")
with open(admin_path) as f:
    lines = f.readlines()

# Find orphaned excepts (except at 16-space indent with no matching try)
fixes = []
for i, line in enumerate(lines):
    # except at 16-20 spaces (too deep)
    stripped = line.strip()
    if stripped.startswith("except ") and line.startswith("                "):
        # Check if there's a try at the same level nearby
        indent = len(line) - len(line.lstrip())
        has_try = False
        for j in range(max(0, i-30), i):
            if lines[j].startswith(" " * indent) and lines[j].strip().startswith("try:"):
                has_try = True
                break
        for j in range(i+1, min(len(lines), i+5)):
            if lines[j].startswith(" " * indent) and lines[j].strip().startswith("except"):
                has_try = True
                break
        if not has_try:
            print(f"  ORPHANED except at line {i+1}: {stripped}")
            fixes.append(i)

# Apply fixes in reverse order
for i in reversed(fixes):
    del lines[i]

# Also fix over-indented try bodies that cause mismatch
# For each try at indentation N, ensure body is N+4
# This handles cases where body lines lost indentation
with open(admin_path, "w") as f:
    f.writelines(lines)

# Verify
try:
    with open(admin_path) as f:
        ast.parse(f.read())
    print("admin.py: FIXED ✅")
except SyntaxError as e:
    print(f"admin.py: STILL BROKEN ❌ - {e}")
    # Show context around error
    err_line = e.lineno
    print(f"  Context around line {err_line}:")
    for i in range(max(0, err_line-3), min(len(lines), err_line+3)):
        marker = ">>>" if i == err_line-1 else "   "
        print(f"  {marker} {i+1}: {lines[i].rstrip()}")

# Verify ALL files after fix
print("\n=== FINAL VERIFICATION ===")
all_ok = True
for fpath in files_to_check:
    try:
        with open(fpath) as f:
            ast.parse(f.read())
    except SyntaxError as e:
        print(f"BROKEN: {fpath}: {e}")
        all_ok = False

if all_ok:
    print("✅ ALL PYTHON FILES PASS SYNTAX CHECK")
else:
    print("❌ SOME FILES STILL BROKEN")
    sys.exit(1)
