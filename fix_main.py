#!/usr/bin/env python3
"""Fix main.py error handling for PermissionError from gspread."""

import sys

with open("/root/Personal-Wallet-Tele-Bot/bot/main.py", "r") as f:
    content = f.read()

changes = 0

# Fix 1: Improve _gsheet_retry to handle PermissionError with no message
old_retry = '                msg = str(exc)\n                if any(t in msg for t in ("429", "quota", "timeout", "deadline", "502", "503")):'
new_retry = '''                msg = str(exc)
                # PermissionError from gspread often has an empty message.
                # Make it clear what the fix is.
                if isinstance(exc, PermissionError) or "PermissionError" in type(exc).__name__:
                    raise PermissionError(
                        "Service account does not have access to the Google Sheet. "
                        "Share the sheet with the SA email as Editor."
                    )
                if any(t in msg for t in ("429", "quota", "timeout", "deadline", "502", "503")):'''

if old_retry in content:
    content = content.replace(old_retry, new_retry)
    print("FIX 1 applied: _gsheet_retry PermissionError handling")
    changes += 1
else:
    print("FIX 1 SKIPPED: pattern not found")

# Fix 2: Improve _err function to handle empty error messages
old_err = 'def _err(action: str, exc: Exception) -> str:\n    msg = str(exc)\n    if "quota" in msg.lower() or "429" in msg:'
new_err = '''def _err(action: str, exc: Exception) -> str:
    msg = str(exc)
    if not msg:
        # gspread PermissionError often has empty message
        if isinstance(exc, PermissionError) or type(exc).__name__ == "PermissionError":
            msg = "Permission denied - the service account does not have access to this Google Sheet. Share the sheet with the SA email as Editor."
        else:
            msg = f"{type(exc).__name__} (no details)"
    if "quota" in msg.lower() or "429" in msg:'''

if old_err in content:
    content = content.replace(old_err, new_err)
    print("FIX 2 applied: _err empty message handling")
    changes += 1
else:
    print("FIX 2 SKIPPED: pattern not found")

if changes == 0:
    print("No changes made - file contents may have changed since analysis")
    sys.exit(1)

with open("/root/Personal-Wallet-Tele-Bot/bot/main.py", "w") as f:
    f.write(content)

print(f"File saved successfully ({changes} changes applied)")
