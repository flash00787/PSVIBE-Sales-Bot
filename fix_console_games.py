#!/usr/bin/env python3
"""Fix: console_games variable → string literal "console_games"."""
import sys

filepath = sys.argv[1]

with open(filepath, 'r') as f:
    c = f.read()

old1 = 'and console_games in result:'
new1 = 'and "console_games" in result:'

old2 = 'return result[console_games]'
new2 = 'return result["console_games"]'

if old1 in c:
    c = c.replace(old1, new1)
    print("Fixed: console_games in result")
if old2 in c:
    c = c.replace(old2, new2)
    print("Fixed: result[console_games]")

with open(filepath, 'w') as f:
    f.write(c)

# Verify
with open(filepath, 'r') as f:
    for i, line in enumerate(f, 1):
        if 'console_games' in line:
            print(f"  Remaining at line {i}: {line.rstrip()[:80]}")

print("Done!")
