#!/usr/bin/env python3
"""Fix print() statements in fix_topup_spam.py -> logger.info()"""

with open("/root/psvibe-sales-bot/fix_topup_spam.py") as f:
    content = f.read()

# Add logging import
content = content.replace(
    "import sys\nimport subprocess",
    "import sys\nimport subprocess\nimport logging\nlogging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger(__name__)",
    1
)

# Replace print( at start of lines with logger.info(
import re
content = re.sub(r"(?m)^(\s*)print\(", r"\1logger.info(", content)

with open("/root/psvibe-sales-bot/fix_topup_spam.py", "w") as f:
    f.write(content)

# Verify
regular_prints = 0
for i, line in enumerate(content.split("\n"), 1):
    stripped = line.strip()
    if stripped.startswith("print(") and not stripped.startswith("print()"):
        # Check it's not in a string or heredoc
        regular_prints += 1
        print(f"  print() at line {i}: {stripped[:60]}")

if regular_prints == 0:
    print("PASS: All print() replaced with logger.info()")
else:
    print(f"WARN: {regular_prints} print() remain (may be in strings)")
