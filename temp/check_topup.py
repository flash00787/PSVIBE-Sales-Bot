#!/usr/bin/env python3
"""Check topup flow in members.py"""
import sys

path = "/root/psvibe-sales-bot/bot/handlers/members.py"
with open(path) as f:
    lines = f.readlines()

# Find step_tu_confirm function
for i, line in enumerate(lines, 1):
    if "async def step_tu_confirm" in line:
        # Print until we see a receipt or reply
        print(f"Found at line {i}")
        end = min(i + 80, len(lines))
        for j in range(i, end):
            print(f"{j}:{lines[j-1]}", end="")
        break

print("\n\n=== Receipt related ===")
for i, line in enumerate(lines, 1):
    if "receipt" in line.lower() and "step_tu" in line:
        print(f"{i}:{line}", end="")
